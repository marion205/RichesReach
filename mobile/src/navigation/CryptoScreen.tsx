/**
 * Crypto Trading Screen
 * Main screen for crypto trading functionality
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery } from '@apollo/client';

// GraphQL Queries
import { GET_CRYPTO_PORTFOLIO, GET_CRYPTO_ANALYTICS } from '../cryptoQueries';

// Components
import ProAaveCard from '../components/forms/ProAaveCard';
import CryptoPortfolioCard from '../components/crypto/CryptoPortfolioCard';
import CryptoTradingCardPro from '../components/crypto/CryptoTradingCardPro';
import CryptoMLSignalsCard from '../components/crypto/CryptoMLSignalsCard';
import DeFiYieldsScreen from '../screens/DeFiYieldsScreen';
import YieldOptimizerScreen from '../screens/YieldOptimizerScreen';

interface CryptoScreenProps {
  navigation: any;
}

const CryptoScreen: React.FC<CryptoScreenProps> = ({ navigation }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'portfolio' | 'trading' | 'aave' | 'signals' | 'yields' | 'optimizer'>('portfolio');
  const [hideBalances, setHideBalances] = useState(false);
  const [tabsLoaded, setTabsLoaded] = useState<Set<string>>(new Set(['portfolio'])); // Track which tabs have been loaded

  // Real GraphQL queries for crypto data
  const { data: portfolioData, loading: portfolioLoading, error: portfolioError, refetch: refetchPortfolio } = useQuery(GET_CRYPTO_PORTFOLIO, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const { data: analyticsData, loading: analyticsLoading, error: analyticsError, refetch: refetchAnalytics } = useQuery(GET_CRYPTO_ANALYTICS, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      // Refetch real data from GraphQL
      await Promise.all([
        refetchPortfolio(),
        refetchAnalytics(),
      ]);
    } catch (error) {
      console.error('Error refreshing crypto data:', error);
    } finally {
      setRefreshing(false);
    }
  }, [refetchPortfolio, refetchAnalytics]);

  const handleTabChange = useCallback((tab: string) => {
    setActiveTab(tab as any);
    setTabsLoaded(prev => new Set([...prev, tab]));
  }, []);

  const renderTabContent = useMemo(() => {
    switch (activeTab) {
      case 'portfolio':
        return (
          <CryptoPortfolioCard 
            portfolio={portfolioData?.cryptoPortfolio}
            analytics={analyticsData?.cryptoAnalytics}
            loading={portfolioLoading || analyticsLoading}
            onRefresh={onRefresh}
            onPressHolding={(symbol) => console.log('Pressed holding:', symbol)}
            onStartTrading={() => setActiveTab('trading')}
            hideBalances={hideBalances}
            onToggleHideBalances={setHideBalances}
            ltvState="CAUTION"
            supportedCurrencies={[
              { symbol: 'BTC', name: 'Bitcoin', iconUrl: 'https://cryptologos.cc/logos/bitcoin-btc-logo.png' },
              { symbol: 'ETH', name: 'Ethereum', iconUrl: 'https://cryptologos.cc/logos/ethereum-eth-logo.png' },
              { symbol: 'SOL', name: 'Solana', iconUrl: 'https://cryptologos.cc/logos/solana-sol-logo.png' }
            ]}
          />
        );
      case 'trading':
        return (
          <CryptoTradingCardPro 
            onTradeSuccess={() => {
              console.log('Trade completed successfully');
            }}
            balances={{
              'BTC': 0.5,
              'ETH': 2.0,
              'USDC': 1000,
            }}
            usdAvailable={5000}
          />
        );
      case 'aave':
        return (
          <ProAaveCard
            brand="RichesReach"
            networkName="Sepolia"
            walletAddress={null} // TODO: Connect to wallet address when available
            backendBaseUrl={process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000"} // Updated to localhost
            explorerTxUrl={(hash) => `https://sepolia.etherscan.io/tx/${hash}`}
            getBalance={async (symbol) => {
              // Mock balance - in production, read from wallet
              return symbol === 'USDC' ? '150.00' : '0.05';
            }}
            getAllowance={async (symbol) => {
              // Mock allowance - in production, read from ERC20 contract
              return '0.00';
            }}
            toFiat={async (symbol, amount) => {
              // Mock USD pricing - in production, use price oracle
              return Number(amount) * (symbol === 'USDC' ? 1 : 2500);
            }}
            onApprove={async ({ symbol, amount }) => {
              // Mock approval - in production, call HybridTransactionService
              return { hash: '0xAPPROVE_' + Date.now() };
            }}
            onSupply={async ({ symbol, amount }) => {
              // Mock supply - in production, call HybridTransactionService
              return { hash: '0xSUPPLY_' + Date.now() };
            }}
            onBorrow={async ({ symbol, amount, rateMode }) => {
              // Mock borrow - in production, call HybridTransactionService
              return { hash: '0xBORROW_' + Date.now() };
            }}
            onSuccess={() => {
              // Refresh data when transactions complete
              console.log('Transaction completed');
            }}
          />
        );
      case 'signals':
        return <CryptoMLSignalsCard initialSymbol="BTC" />;
      case 'yields':
        return <DeFiYieldsScreen navigation={navigation} onTabChange={handleTabChange} />;
      case 'optimizer':
        return <YieldOptimizerScreen navigation={navigation} />;
      default:
        return null;
    }
  }, [activeTab, portfolioData, analyticsData, navigation]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Crypto DeFi</Text>
        <Pressable onPress={() => setHideBalances(!hideBalances)} style={styles.hideButton}>
          <Icon name={hideBalances ? 'eye-off' : 'eye'} size={20} color="#fff" />
        </Pressable>
      </View>

      <View style={styles.tabContainer}>
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.tabContentContainer}
        >
          <Pressable
            style={[styles.tabButton, activeTab === 'portfolio' && styles.activeTab]}
            onPress={() => handleTabChange('portfolio')}
            hitSlop={10}
          >
            <Icon name="pie-chart" size={16} color={activeTab === 'portfolio' ? '#2563EB' : '#6B7280'} />
            <Text 
              style={[styles.tabText, activeTab === 'portfolio' && styles.activeTabText]}
              numberOfLines={1}
              allowFontScaling={false}
            >
              Portfolio
            </Text>
          </Pressable>
          <Pressable
            style={[styles.tabButton, activeTab === 'trading' && styles.activeTab]}
            onPress={() => handleTabChange('trading')}
            hitSlop={10}
          >
            <Icon name="trending-up" size={16} color={activeTab === 'trading' ? '#2563EB' : '#6B7280'} />
            <Text 
              style={[styles.tabText, activeTab === 'trading' && styles.activeTabText]}
              numberOfLines={1}
              allowFontScaling={false}
            >
              Trading
            </Text>
          </Pressable>
          <Pressable
            style={[styles.tabButton, activeTab === 'aave' && styles.activeTab]}
            onPress={() => handleTabChange('aave')}
            hitSlop={10}
          >
            <Icon name="activity" size={16} color={activeTab === 'aave' ? '#2563EB' : '#6B7280'} />
            <Text 
              style={[styles.tabText, activeTab === 'aave' && styles.activeTabText]}
              numberOfLines={1}
              allowFontScaling={false}
            >
              AAVE
            </Text>
          </Pressable>
          <Pressable
            style={[styles.tabButton, activeTab === 'signals' && styles.activeTab]}
            onPress={() => handleTabChange('signals')}
            hitSlop={10}
          >
            <Icon name="activity" size={16} color={activeTab === 'signals' ? '#2563EB' : '#6B7280'} />
            <Text 
              style={[styles.tabText, activeTab === 'signals' && styles.activeTabText]}
              numberOfLines={1}
              allowFontScaling={false}
            >
              Signals
            </Text>
          </Pressable>
          <Pressable
            style={[styles.tabButton, activeTab === 'yields' && styles.activeTab]}
            onPress={() => handleTabChange('yields')}
            hitSlop={10}
          >
            <Icon name="trending-up" size={16} color={activeTab === 'yields' ? '#2563EB' : '#6B7280'} />
            <Text 
              style={[styles.tabText, activeTab === 'yields' && styles.activeTabText]}
              numberOfLines={1}
              allowFontScaling={false}
            >
              Yields
            </Text>
          </Pressable>
          <Pressable
            style={[styles.tabButton, activeTab === 'optimizer' && styles.activeTab]}
            onPress={() => handleTabChange('optimizer')}
            hitSlop={10}
          >
            <Icon name="cpu" size={16} color={activeTab === 'optimizer' ? '#2563EB' : '#6B7280'} />
            <Text 
              style={[styles.tabText, activeTab === 'optimizer' && styles.activeTabText]}
              numberOfLines={1}
              allowFontScaling={false}
            >
              AI Optimizer
            </Text>
          </Pressable>
        </ScrollView>
      </View>

      {activeTab === 'yields' || activeTab === 'optimizer' ? (
        // Use View for tabs with FlatList to avoid VirtualizedList nesting
        <View style={styles.contentContainer}>
          {renderTabContent}
        </View>
      ) : (
        // Use ScrollView for other tabs
        <ScrollView
          style={styles.contentContainer}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
          {renderTabContent}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    backgroundColor: '#343a40',
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  hideButton: {
    padding: 5,
  },
  tabContainer: {
    paddingVertical: 8,
    backgroundColor: 'transparent',
  },
  tabContentContainer: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 8,
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 12,
  },
  activeTab: {
    backgroundColor: 'rgba(37, 99, 235, 0.10)',
  },
  tabText: {
    marginLeft: 6,
    marginTop: 1,
    fontSize: 14,
    fontWeight: '500',
    color: '#6B7280',
    includeFontPadding: false,
    textAlignVertical: 'center',
  },
  activeTabText: {
    color: '#2563EB',
    fontWeight: '600',
  },
  contentContainer: {
    flex: 1,
    padding: 10,
  },
  placeholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  placeholderText: {
    fontSize: 16,
    color: '#6c757d',
    textAlign: 'center',
  },
});

export default CryptoScreen;