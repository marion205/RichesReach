import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import EducationalTooltip from './EducationalTooltip';
import { getTermExplanation } from '../data/financialTerms';

interface Holding {
  symbol: string;
  companyName: string;
  shares: number;
  currentPrice: number;
  totalValue: number;
  costBasis: number;
  returnAmount: number;
  returnPercent: number;
  sector: string;
}

interface PortfolioHoldingsProps {
  holdings: Holding[];
  onStockPress?: (symbol: string) => void;
}

export default function PortfolioHoldings({ holdings, onStockPress }: PortfolioHoldingsProps) {
  const formatCurrency = (amount: number) => {
    return `$${amount.toLocaleString('en-US', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    })}`;
  };

  const formatPercent = (percent: number) => {
    const isPositive = percent >= 0;
    return `${isPositive ? '+' : ''}${percent.toFixed(2)}%`;
  };

  const getReturnColor = (amount: number) => {
    return amount >= 0 ? '#34C759' : '#FF3B30';
  };

  const getReturnIcon = (amount: number) => {
    return amount >= 0 ? 'trending-up' : 'trending-down';
  };

  if (!holdings || holdings.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Icon name="pie-chart" size={48} color="#8E8E93" />
        <Text style={styles.emptyTitle}>No Holdings</Text>
        <Text style={styles.emptySubtitle}>Add stocks to your portfolio to see holdings</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Your Holdings</Text>
        <Text style={styles.subtitle}>{holdings.length} positions</Text>
      </View>
      
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {holdings.map((holding, index) => (
          <TouchableOpacity
            key={`${holding.symbol}-${index}`}
            style={styles.holdingCard}
            onPress={() => onStockPress?.(holding.symbol)}
            activeOpacity={0.7}
          >
            <View style={styles.cardHeader}>
              <View style={styles.stockInfo}>
                <Text style={styles.symbol}>{holding.symbol}</Text>
                <Text style={styles.companyName} numberOfLines={1}>
                  {holding.companyName}
                </Text>
              </View>
              <View style={styles.sectorBadge}>
                <Text style={styles.sectorText}>{holding.sector}</Text>
              </View>
            </View>
            
            <View style={styles.cardBody}>
              <View style={styles.positionInfo}>
                <EducationalTooltip
                  term="Shares"
                  explanation={getTermExplanation('Share')}
                  position="top"
                >
                  <Text style={styles.sharesText}>{holding.shares} shares</Text>
                </EducationalTooltip>
                <EducationalTooltip
                  term="Current Price"
                  explanation={getTermExplanation('Current Price')}
                  position="top"
                >
                  <Text style={styles.priceText}>{formatCurrency(holding.currentPrice)}</Text>
                </EducationalTooltip>
              </View>
              
              <View style={styles.valueInfo}>
                <EducationalTooltip
                  term="Total Value"
                  explanation={getTermExplanation('Total Value')}
                  position="top"
                >
                  <Text style={styles.valueText}>{formatCurrency(holding.totalValue)}</Text>
                </EducationalTooltip>
                <EducationalTooltip
                  term="Return Percentage"
                  explanation={getTermExplanation('Return Percentage')}
                  position="top"
                >
                  <View style={styles.returnContainer}>
                    <Icon 
                      name={getReturnIcon(holding.returnAmount)} 
                      size={12} 
                      color={getReturnColor(holding.returnAmount)} 
                    />
                    <Text style={[styles.returnText, { color: getReturnColor(holding.returnAmount) }]}>
                      {formatPercent(holding.returnPercent)}
                    </Text>
                  </View>
                </EducationalTooltip>
              </View>
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  subtitle: {
    fontSize: 14,
    color: '#8E8E93',
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  holdingCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginRight: 12,
    width: 200,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  stockInfo: {
    flex: 1,
  },
  symbol: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 2,
  },
  companyName: {
    fontSize: 12,
    color: '#8E8E93',
    lineHeight: 16,
  },
  sectorBadge: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  sectorText: {
    fontSize: 10,
    color: '#1976D2',
    fontWeight: '600',
  },
  cardBody: {
    gap: 8,
  },
  positionInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sharesText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  priceText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  valueInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  valueText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  returnContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  returnText: {
    fontSize: 12,
    fontWeight: '600',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 40,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 12,
    marginBottom: 4,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
  },
});
