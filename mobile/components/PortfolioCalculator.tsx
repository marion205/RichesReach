import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface Stock {
  id: string;
  symbol: string;
  companyName: string;
  currentPrice?: number;
}

interface PortfolioCalculatorProps {
  watchlistItems: Array<{
    id: string;
    stock: Stock;
    addedAt: string;
    notes?: string;
  }>;
}

interface PortfolioItem {
  stockId: string;
  symbol: string;
  companyName: string;
  shares: number;
  currentPrice: number;
  totalValue: number;
}

const PortfolioCalculator: React.FC<PortfolioCalculatorProps> = ({ watchlistItems }) => {
  const [portfolioItems, setPortfolioItems] = useState<PortfolioItem[]>([]);
  const [totalPortfolioValue, setTotalPortfolioValue] = useState(0);
  const [isEditing, setIsEditing] = useState(false);

  // Mock current prices (in real app, these would come from API)
  const mockPrices: { [key: string]: number } = {
    'AAPL': 185.50,
    'MSFT': 375.20,
    'GOOGL': 142.80,
    'AMZN': 155.30,
    'TSLA': 245.60,
    'NVDA': 485.90,
    'META': 380.25,
    'NFLX': 485.20,
    'AMD': 125.40,
    'INTC': 45.80,
  };

  useEffect(() => {
    initializePortfolio();
  }, [watchlistItems]);

  const initializePortfolio = () => {
    const initialItems = watchlistItems.map(item => ({
      stockId: item.stock.id,
      symbol: item.stock.symbol,
      companyName: item.stock.companyName,
      shares: 0,
      currentPrice: mockPrices[item.stock.symbol] || 100,
      totalValue: 0,
    }));
    setPortfolioItems(initialItems);
    calculateTotalValue(initialItems);
  };

  const calculateTotalValue = (items: PortfolioItem[]) => {
    const total = items.reduce((sum, item) => sum + item.totalValue, 0);
    setTotalPortfolioValue(total);
  };

  const updateShares = (stockId: string, shares: number) => {
    const updatedItems = portfolioItems.map(item => {
      if (item.stockId === stockId) {
        const totalValue = shares * item.currentPrice;
        return { ...item, shares, totalValue };
      }
      return item;
    });
    setPortfolioItems(updatedItems);
    calculateTotalValue(updatedItems);
  };

  const quickAddShares = (stockId: string, amount: number) => {
    const currentItem = portfolioItems.find(item => item.stockId === stockId);
    if (currentItem) {
      const newShares = Math.max(0, currentItem.shares + amount);
      updateShares(stockId, newShares);
    }
  };

  const resetPortfolio = () => {
    Alert.alert(
      'Reset Portfolio',
      'Are you sure you want to reset all share quantities to 0?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: () => {
            const resetItems = portfolioItems.map(item => ({
              ...item,
              shares: 0,
              totalValue: 0,
            }));
            setPortfolioItems(resetItems);
            setTotalPortfolioValue(0);
          },
        },
      ]
    );
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Icon name="bar-chart-2" size={20} color="#34C759" />
          <Text style={styles.title}>Portfolio Calculator</Text>
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity
            style={styles.editButton}
            onPress={() => setIsEditing(!isEditing)}
          >
            <Icon name={isEditing ? "check" : "edit"} size={16} color="#34C759" />
            <Text style={styles.editButtonText}>
              {isEditing ? "Done" : "Edit"}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.resetButton} onPress={resetPortfolio}>
            <Icon name="refresh-cw" size={16} color="#FF3B30" />
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.totalValueContainer}>
        <Text style={styles.totalValueLabel}>Total Portfolio Value</Text>
        <Text style={styles.totalValueAmount}>{formatCurrency(totalPortfolioValue)}</Text>
      </View>

      <ScrollView style={styles.stocksList} showsVerticalScrollIndicator={false}>
        {portfolioItems.map((item) => (
          <View key={item.stockId} style={styles.stockItem}>
            <View style={styles.stockInfo}>
              <View style={styles.stockHeader}>
                <Text style={styles.symbol}>{item.symbol}</Text>
                <Text style={styles.price}>{formatCurrency(item.currentPrice)}</Text>
              </View>
              <Text style={styles.companyName} numberOfLines={1}>
                {item.companyName}
              </Text>
            </View>

            <View style={styles.sharesSection}>
              {isEditing ? (
                <View style={styles.sharesInputContainer}>
                  <Text style={styles.sharesLabel}>Shares:</Text>
                  <TextInput
                    style={styles.sharesInput}
                    value={item.shares.toString()}
                    onChangeText={(text) => {
                      const shares = parseInt(text) || 0;
                      updateShares(item.stockId, shares);
                    }}
                    keyboardType="numeric"
                    placeholder="0"
                    maxLength={6}
                  />
                </View>
              ) : (
                <View style={styles.sharesDisplay}>
                  <Text style={styles.sharesText}>{item.shares} shares</Text>
                </View>
              )}

              <View style={styles.totalValue}>
                <Text style={styles.totalValueText}>
                  {formatCurrency(item.totalValue)}
                </Text>
              </View>
            </View>

            {isEditing && (
              <View style={styles.quickAddButtons}>
                <TouchableOpacity
                  style={styles.quickAddButton}
                  onPress={() => quickAddShares(item.stockId, 1)}
                >
                  <Text style={styles.quickAddText}>+1</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.quickAddButton}
                  onPress={() => quickAddShares(item.stockId, 10)}
                >
                  <Text style={styles.quickAddText}>+10</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.quickAddButton}
                  onPress={() => quickAddShares(item.stockId, 100)}
                >
                  <Text style={styles.quickAddText}>+100</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.quickAddButton, styles.removeButton]}
                  onPress={() => quickAddShares(item.stockId, -1)}
                >
                  <Text style={styles.quickAddText}>-1</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        ))}
      </ScrollView>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          💡 Tap "Edit" to input share quantities and see real-time portfolio values
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    marginHorizontal: 16,
    marginVertical: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  editButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#F2F2F7',
    borderRadius: 16,
  },
  editButtonText: {
    fontSize: 14,
    color: '#34C759',
    fontWeight: '500',
  },
  resetButton: {
    padding: 6,
    backgroundColor: '#FFE5E5',
    borderRadius: 16,
  },
  totalValueContainer: {
    alignItems: 'center',
    marginBottom: 20,
    paddingVertical: 16,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
  },
  totalValueLabel: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  totalValueAmount: {
    fontSize: 28,
    fontWeight: '700',
    color: '#34C759',
  },
  stocksList: {
    maxHeight: 300,
  },
  stockItem: {
    borderBottomWidth: 1,
    borderBottomColor: '#F2F2F7',
    paddingVertical: 12,
  },
  stockInfo: {
    marginBottom: 8,
  },
  stockHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  symbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  price: {
    fontSize: 14,
    fontWeight: '500',
    color: '#34C759',
  },
  companyName: {
    fontSize: 12,
    color: '#8E8E93',
  },
  sharesSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sharesInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  sharesLabel: {
    fontSize: 14,
    color: '#8E8E93',
  },
  sharesInput: {
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    fontSize: 14,
    minWidth: 60,
    textAlign: 'center',
    backgroundColor: '#FFFFFF',
  },
  sharesDisplay: {
    minWidth: 80,
  },
  sharesText: {
    fontSize: 14,
    color: '#1C1C1E',
    fontWeight: '500',
  },
  totalValue: {
    minWidth: 80,
    alignItems: 'flex-end',
  },
  totalValueText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  quickAddButtons: {
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'flex-end',
  },
  quickAddButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#F2F2F7',
    borderRadius: 16,
    minWidth: 40,
    alignItems: 'center',
  },
  removeButton: {
    backgroundColor: '#FFE5E5',
  },
  quickAddText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  footer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#F2F2F7',
  },
  footerText: {
    fontSize: 12,
    color: '#8E8E93',
    textAlign: 'center',
    fontStyle: 'italic',
  },
});

export default PortfolioCalculator;
