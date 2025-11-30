import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface OptionsEducationTooltipProps {
  topic: 'delta' | 'theta' | 'iv' | 'spread' | 'greeks' | 'strike';
  onDismiss?: () => void;
}

const EDUCATION_CONTENT = {
  delta: {
    title: 'Delta',
    explanation: 'How much the option price moves when the stock moves $1. A delta of 0.5 means the option moves $0.50 for every $1 the stock moves.',
    example: 'AAPL at $150, call with delta 0.5. If AAPL goes to $151, the call goes up ~$0.50.',
  },
  theta: {
    title: 'Theta',
    explanation: 'Time decay. How much value the option loses each day. Negative theta means you lose money over time.',
    example: 'Theta of -0.05 means you lose $5 per day per contract (100 shares).',
  },
  iv: {
    title: 'Implied Volatility',
    explanation: 'How much the market expects the stock to move. High IV = expensive options. Low IV = cheaper options.',
    example: 'IV of 30% means the market expects ±30% moves. Higher IV = higher option prices.',
  },
  spread: {
    title: 'Bid-Ask Spread',
    explanation: 'The difference between what buyers will pay (bid) and sellers want (ask). Tighter spreads = better prices.',
    example: 'Bid $2.40, Ask $2.50 = $0.10 spread. You buy at $2.50, sell at $2.40 = instant $0.10 loss.',
  },
  greeks: {
    title: 'The Greeks',
    explanation: 'Five metrics that show how options prices change: Delta (price), Gamma (delta change), Theta (time), Vega (volatility), Rho (interest rates).',
    example: 'Think of them as dials that control option prices. Learn them one at a time.',
  },
  strike: {
    title: 'Strike Price',
    explanation: 'The price at which you can buy (call) or sell (put) the stock. In-the-money = profitable now. Out-of-the-money = needs stock to move.',
    example: 'AAPL at $150. $145 call is in-the-money (worth $5). $155 call is out-of-the-money (worthless unless AAPL goes above $155).',
  },
};

export default function OptionsEducationTooltip({ topic, onDismiss }: OptionsEducationTooltipProps) {
  const content = EDUCATION_CONTENT[topic];

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.iconContainer}>
          <Icon name="book-open" size={20} color="#007AFF" />
        </View>
        <Text style={styles.title}>{content.title}</Text>
        {onDismiss && (
          <TouchableOpacity onPress={onDismiss} style={styles.closeButton}>
            <Icon name="x" size={18} color="#6B7280" />
          </TouchableOpacity>
        )}
      </View>

      <Text style={styles.explanation}>{content.explanation}</Text>
      
      <View style={styles.exampleContainer}>
        <Text style={styles.exampleLabel}>Example:</Text>
        <Text style={styles.exampleText}>{content.example}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F0F7FF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#DBEAFE',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#DBEAFE',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
  },
  closeButton: {
    padding: 4,
  },
  explanation: {
    fontSize: 15,
    color: '#374151',
    lineHeight: 22,
    marginBottom: 12,
  },
  exampleContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#007AFF',
  },
  exampleLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 4,
  },
  exampleText: {
    fontSize: 14,
    color: '#111827',
    lineHeight: 20,
  },
});


