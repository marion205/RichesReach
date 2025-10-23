import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Holding {
  symbol: string;
  quantity: number;
  currentPrice: number;
  totalValue: number;
  change: number;
  changePercent: number;
}

interface PortfolioHoldingsProps {
  holdings: Holding[];
  onStockPress: (symbol: string) => void;
}

const PortfolioHoldings: React.FC<PortfolioHoldingsProps> = ({ 
  holdings, 
  onStockPress 
}) => {
  if (!holdings || holdings.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Ionicons name="pie-chart-outline" size={48} color="#666" />
        <Text style={styles.emptyText}>No holdings available</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Portfolio Holdings</Text>
      {holdings.map((holding, index) => (
        <TouchableOpacity
          key={`${holding.symbol}-${index}`}
          style={styles.holdingItem}
          onPress={() => onStockPress(holding.symbol)}
        >
          <View style={styles.holdingInfo}>
            <Text style={styles.symbol}>{holding.symbol}</Text>
            <Text style={styles.quantity}>{holding.quantity} shares</Text>
          </View>
          <View style={styles.holdingValue}>
            <Text style={styles.totalValue}>
              ${(holding.totalValue || 0).toFixed(2)}
            </Text>
            <Text style={[
              styles.change,
              { color: (holding.change || 0) >= 0 ? '#4CAF50' : '#F44336' }
            ]}>
              {(holding.change || 0) >= 0 ? '+' : ''}${(holding.change || 0).toFixed(2)} 
              ({(holding.changePercent || 0) >= 0 ? '+' : ''}{(holding.changePercent || 0).toFixed(2)}%)
            </Text>
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  holdingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  holdingInfo: {
    flex: 1,
  },
  symbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  quantity: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  holdingValue: {
    alignItems: 'flex-end',
  },
  totalValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  change: {
    fontSize: 14,
    marginTop: 2,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
    backgroundColor: '#fff',
    borderRadius: 12,
    marginVertical: 8,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    marginTop: 8,
  },
});

export default PortfolioHoldings;
