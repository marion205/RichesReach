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
import { useMutation, useApolloClient } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const SAVE_PORTFOLIO = gql`
  mutation SavePortfolio($stockIds: [ID!]!, $sharesList: [Int!]!, $notesList: [String!], $currentPrices: [Float!]) {
    savePortfolio(stockIds: $stockIds, sharesList: $sharesList, notesList: $notesList, currentPrices: $currentPrices) {
      success
      message
      portfolio {
        id
        stock {
          symbol
          companyName
        }
        shares
        totalValue
      }
    }
  }
`;

const GET_CURRENT_STOCK_PRICES = gql`
  query GetCurrentStockPrices($symbols: [String!]!) {
    currentStockPrices(symbols: $symbols) {
      symbol
      currentPrice
      change
      changePercent
      lastUpdated
      source
      verified
      apiResponse
    }
  }
`;

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
  onPortfolioUpdate?: (newValue: number) => void;
}

interface PortfolioItem {
  stockId: string;
  symbol: string;
  companyName: string;
  shares: number;
  currentPrice: number;
  totalValue: number;
}

const PortfolioCalculator: React.FC<PortfolioCalculatorProps> = ({ watchlistItems, onPortfolioUpdate }) => {
  const [portfolioItems, setPortfolioItems] = useState<PortfolioItem[]>([]);
  const [totalPortfolioValue, setTotalPortfolioValue] = useState(0);
  const [isEditing, setIsEditing] = useState(false);
  const [stockPrices, setStockPrices] = useState<{ [key: string]: number }>({});
  const [pricesLoading, setPricesLoading] = useState(false);

  const [savePortfolio, { loading: savingPortfolio }] = useMutation(SAVE_PORTFOLIO);
  const client = useApolloClient();

  // Fallback prices if API fails (these will be replaced by real data)
  const fallbackPrices: { [key: string]: number } = {
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

  useEffect(() => {
    if (watchlistItems.length > 0) {
      fetchCurrentStockPrices();
    }
  }, [watchlistItems]);

  // Update portfolio items when stock prices change
  useEffect(() => {
    if (Object.keys(stockPrices).length > 0) {
      updatePortfolioPrices();
    }
  }, [stockPrices]);

  const fetchCurrentStockPrices = async () => {
    if (watchlistItems.length === 0) return;
    
    setPricesLoading(true);
    try {
      const symbols = watchlistItems.map(item => item.stock.symbol);
      
      const result = await client.query({
        query: GET_CURRENT_STOCK_PRICES,
        variables: { symbols },
        fetchPolicy: 'no-cache'  // Force fresh data every time
      });
      
      if (result.data?.currentStockPrices) {
        const newPrices: { [key: string]: number } = {};
        result.data.currentStockPrices.forEach((price: any) => {
          if (price.currentPrice) {
            newPrices[price.symbol] = price.currentPrice;
          }
        });
        
        setStockPrices(newPrices);
      }
    } catch (error) {
      console.error('Could not fetch real stock prices, using fallback data:', error);
      setStockPrices(fallbackPrices);
    } finally {
      setPricesLoading(false);
    }
  };

  const initializePortfolio = () => {
    const initialItems = watchlistItems.map(item => ({
      stockId: item.stock.id,
      symbol: item.stock.symbol,
      companyName: item.stock.companyName,
      shares: 0,
      currentPrice: stockPrices[item.stock.symbol] || fallbackPrices[item.stock.symbol] || 100,
      totalValue: 0,
    }));
    setPortfolioItems(initialItems);
    calculateTotalValue(initialItems);
  };

  const updatePortfolioPrices = () => {
    const updatedItems = portfolioItems.map(item => ({
      ...item,
      currentPrice: stockPrices[item.symbol] || fallbackPrices[item.symbol] || item.currentPrice,
      totalValue: item.shares * (stockPrices[item.symbol] || fallbackPrices[item.symbol] || item.currentPrice)
    }));
    setPortfolioItems(updatedItems);
    calculateTotalValue(updatedItems);
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

  const handleDoneClick = async () => {
    try {
      // Prepare portfolio data for saving in new format - only items with shares > 0
      const validItems = portfolioItems.filter(item => item.shares > 0);
      const stockIds = validItems.map(item => item.stockId);
      const sharesList = validItems.map(item => item.shares);
      const notesList = validItems.map(item => '');
      
      // Also save current prices to update Stock model
      const currentPrices = validItems.map(item => item.currentPrice);

      // Debug logging
      console.log('🔍 Saving portfolio with data:');
      console.log('  stockIds:', stockIds);
      console.log('  sharesList:', sharesList);
      console.log('  currentPrices:', currentPrices);
      console.log('  portfolioItems:', portfolioItems);

      // Validate data before sending
      if (stockIds.length === 0) {
        Alert.alert('Error', 'No stocks to save');
        return;
      }

      // Filter out items with 0 shares
      if (validItems.length === 0) {
        Alert.alert('Error', 'Please add shares to at least one stock');
        return;
      }

      console.log('SUCCESS: Valid items to save:', validItems.length);

      const result = await savePortfolio({
        variables: { 
          stockIds,
          sharesList,
          notesList,
          currentPrices
        }
      });

      if (result.data?.savePortfolio?.success) {
        // Update portfolio value in cache immediately
        try {
          // Calculate new portfolio value
          const newPortfolioValue = validItems.reduce((total, item) => {
            return total + (item.shares * item.currentPrice);
          }, 0);
          
          // Use cache.modify to update the portfolio value directly
          client.cache.modify({
            fields: {
              portfolioValue: () => newPortfolioValue
            }
          });
          
          console.log('SUCCESS: Portfolio value updated in cache:', newPortfolioValue);
          
          // Debug: Check cache state
          const cacheData = client.readQuery({
            query: gql`
              query GetPortfolioValue {
                portfolioValue
              }
            `
          });
          console.log('🔍 Cache data after update:', cacheData);
          
          // Notify parent component of portfolio update
          if (onPortfolioUpdate) {
            onPortfolioUpdate(newPortfolioValue);
          }
        } catch (error) {
          console.log('WARNING: Could not update portfolio value in cache:', error);
        }
        
        setIsEditing(false);
      } else {
        console.log('ERROR: Portfolio save failed:', result.data?.savePortfolio?.message);
      }
    } catch (error) {
      console.error('ERROR: Portfolio save error:', error);
      console.error('ERROR: Error details:', JSON.stringify(error, null, 2));
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
        </View>
        <View style={styles.headerRight}>
          {!isEditing && (
            <TouchableOpacity
              style={styles.refreshButton}
              onPress={fetchCurrentStockPrices}
              disabled={pricesLoading}
            >
              <Icon 
                name={pricesLoading ? "loader" : "refresh-cw"} 
                size={16} 
                color={pricesLoading ? "#C7C7CC" : "#fff"} 
              />
              <Text style={[styles.refreshButtonText, pricesLoading && styles.disabledText]}>
                {pricesLoading ? 'Updating...' : 'Refresh'}
              </Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity
            style={styles.editButton}
            onPress={() => {
              if (isEditing) {
                handleDoneClick();
              } else {
                setIsEditing(true);
              }
            }}
            disabled={savingPortfolio}
          >
            <Icon name={isEditing ? "check" : "edit"} size={16} color="#34C759" />
            <Text style={styles.editButtonText}>
              {isEditing ? (savingPortfolio ? "Saving..." : "Done") : "Edit"}
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
        <Text style={styles.subtitle}>Portfolio Calculator</Text>
        {pricesLoading && (
          <Text style={styles.rateLimitNote}>
            🔄 Fetching live prices...
          </Text>
        )}
        {!pricesLoading && Object.keys(stockPrices).length === 0 && (
          <Text style={styles.rateLimitNote}>
            WARNING: Using stored prices (API rate limit reached)
          </Text>
        )}
      </View>

      <ScrollView style={styles.stocksList} showsVerticalScrollIndicator={false}>
        {portfolioItems.map((item) => (
          <View key={item.stockId} style={styles.stockItem}>
            <View style={styles.stockInfo}>
              <View style={styles.stockHeader}>
                <Text style={styles.symbol}>{item.symbol}</Text>
                <View style={styles.priceContainer}>
                  <Text style={styles.price}>{formatCurrency(item.currentPrice)}</Text>
                  {stockPrices[item.symbol] && (
                    <Text style={styles.priceSource}>Live</Text>
                  )}
                </View>
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
           Tap "Edit" to input share quantities and see real-time portfolio values. Click "Done" to save your portfolio.
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
    alignItems: 'flex-start',
    marginBottom: 16,
    flexWrap: 'wrap',
    gap: 8,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    maxWidth: '15%',
    flexShrink: 0,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    flexWrap: 'nowrap',
    maxWidth: '80%',
    justifyContent: 'flex-end',
    flexShrink: 0,
  },
  editButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 6,
    backgroundColor: '#F2F2F7',
    borderRadius: 16,
    minWidth: 55,
  },
  editButtonText: {
    fontSize: 14,
    color: '#34C759',
    fontWeight: '500',
  },
  resetButton: {
    padding: 4,
    backgroundColor: '#FFE5E5',
    borderRadius: 16,
    minWidth: 32,
    alignItems: 'center',
    justifyContent: 'center',
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
  subtitle: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 4,
    fontStyle: 'italic',
  },
  rateLimitNote: {
    fontSize: 11,
    color: '#FF9500',
    marginTop: 4,
    textAlign: 'center',
    fontStyle: 'italic',
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
  priceContainer: {
    alignItems: 'flex-end',
  },
  price: {
    fontSize: 14,
    fontWeight: '500',
    color: '#34C759',
  },
  priceSource: {
    fontSize: 10,
    fontWeight: '600',
    color: '#34C759',
    backgroundColor: '#E8F5E8',
    paddingHorizontal: 4,
    paddingVertical: 2,
    borderRadius: 4,
    textAlign: 'center',
    marginTop: 2,
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
  refreshButton: {
    backgroundColor: '#34C759',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 0,
    minWidth: 65,
  },
  refreshButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 4,
  },
  disabledText: {
    color: '#C7C7CC',
  },
});

export default PortfolioCalculator;
