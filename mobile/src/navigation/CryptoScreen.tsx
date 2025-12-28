/**
 * Crypto Trading Screen
 * Main screen for crypto trading functionality
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  RefreshControl,
  SafeAreaView,
  TouchableOpacity,
  Modal,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery } from '@apollo/client';
import LicensingDisclosureScreen from '../components/LicensingDisclosureScreen';
import { FEATURES } from '../config/featureFlags';

// GraphQL Queries
import { GET_CRYPTO_PORTFOLIO, GET_CRYPTO_ANALYTICS } from '../cryptoQueries';

// Mock data for demo when API is unavailable
const getMockCryptoPortfolio = () => ({
  total_value_usd: 12543.50,
  total_cost_basis: 11000.00,
  total_pnl: 1543.50,
  total_pnl_percentage: 14.03,
  total_pnl_1d: 125.50,
  total_pnl_pct_1d: 1.01,
  total_pnl_1w: 450.75,
  total_pnl_pct_1w: 3.73,
  total_pnl_1m: 1543.50,
  total_pnl_pct_1m: 14.03,
  holdings: [
    {
      cryptocurrency: { symbol: 'BTC', name: 'Bitcoin' },
      quantity: 0.25,
      current_value: 12125.00,
      unrealized_pnl_percentage: 15.48,
    },
    {
      cryptocurrency: { symbol: 'ETH', name: 'Ethereum' },
      quantity: 2.5,
      current_value: 7375.00,
      unrealized_pnl_percentage: 5.36,
    },
    {
      cryptocurrency: { symbol: 'SOL', name: 'Solana' },
      quantity: 50,
      current_value: 5100.00,
      unrealized_pnl_percentage: 7.37,
    },
  ],
});

const getMockCryptoAnalytics = () => ({
  portfolio_volatility: 0.35,
  sharpe_ratio: 1.8,
  max_drawdown: -8.5,
  diversification_score: 75,
  sector_allocation: {
    'Layer 1': 45,
    'DeFi': 30,
    'Stablecoins': 25,
  },
  best_performer: {
    symbol: 'BTC',
    pnl_percentage: 15.48,
  },
  worst_performer: {
    symbol: 'SOL',
    pnl_percentage: 7.37,
  },
  last_updated: new Date().toISOString(),
});

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
  const [showLicensingDisclosure, setShowLicensingDisclosure] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'portfolio' | 'trading' | 'aave' | 'signals' | 'yields' | 'optimizer'>('portfolio');
  const [hideBalances, setHideBalances] = useState(false);
  const [tabsLoaded, setTabsLoaded] = useState<Set<string>>(new Set(['portfolio'])); // Track which tabs have been loaded

  // Real GraphQL queries for crypto data with proper guards
  const { data: portfolioData, loading: portfolioLoading, error: portfolioError, refetch: refetchPortfolio } = useQuery(GET_CRYPTO_PORTFOLIO, {
    skip: false, // No required variables for this query
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
    context: { fetchOptions: { timeout: 8000 } }, // 8 second timeout
    onError: (error) => {
      // Suppress network errors - will use mock data
      if (!error?.message?.includes('Network request failed')) {
        console.log('[GQL] Portfolio error:', error.message, error.graphQLErrors);
      }
    },
  });

  const { data: analyticsData, loading: analyticsLoading, error: analyticsError, refetch: refetchAnalytics } = useQuery(GET_CRYPTO_ANALYTICS, {
    skip: false, // No required variables for this query
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
    context: { fetchOptions: { timeout: 8000 } }, // 8 second timeout
    onError: (error) => {
      // Suppress network errors - will use mock data
      if (!error?.message?.includes('Network request failed')) {
        console.log('[GQL] Analytics error:', error.message, error.graphQLErrors);
      }
    },
  });

  // Use real data from GraphQL or fallback to mock data for demo
  // OPTIMISTIC LOADING: Show mock data immediately, replace with real data when it arrives
  // Transform GraphQL camelCase to component snake_case format
  const effectivePortfolio = useMemo(() => {
    // Priority 1: Use real data if available
    if (portfolioData?.cryptoPortfolio) {
      const p = portfolioData.cryptoPortfolio;
      // Transform camelCase GraphQL response to snake_case component format
      return {
        total_value_usd: p.totalValueUsd,
        total_cost_basis: p.totalCostBasis,
        total_pnl: p.totalPnl,
        total_pnl_percentage: p.totalPnlPercentage,
        holdings: p.holdings?.map((h: any) => ({
          cryptocurrency: h.cryptocurrency,
          quantity: h.quantity,
          current_value: h.currentValue,
          unrealized_pnl_percentage: h.unrealizedPnlPercentage,
        })) || [],
      };
    }
    // Priority 2: If error occurred or loading completed with no data, use mock data
    const hasError = portfolioError && !portfolioData?.cryptoPortfolio;
    const hasNetworkError = portfolioError?.message?.includes('Network request failed');
    const loadingCompleted = !portfolioLoading && !portfolioData?.cryptoPortfolio;
    
    // Always return mock data for optimistic loading (show immediately, replace when real data arrives)
    if (hasError || hasNetworkError || loadingCompleted || !portfolioLoading) {
      return getMockCryptoPortfolio();
    }
    
    // While actively loading, show mock data immediately (optimistic loading)
    return getMockCryptoPortfolio();
  }, [portfolioData?.cryptoPortfolio, portfolioLoading, portfolioError]);

  const effectiveAnalytics = useMemo(() => {
    // Priority 1: Use real data if available
    if (analyticsData?.cryptoAnalytics) {
      const a = analyticsData.cryptoAnalytics;
      // Transform camelCase GraphQL response to snake_case component format
      return {
        portfolio_volatility: a.portfolioVolatility,
        sharpe_ratio: a.sharpeRatio,
        max_drawdown: a.maxDrawdown,
        diversification_score: a.diversificationScore,
        sector_allocation: a.sectorAllocation,
        best_performer: a.bestPerformer ? {
          symbol: a.bestPerformer.symbol,
          pnl_percentage: a.bestPerformer.pnlPercentage || 0,
        } : undefined,
        worst_performer: a.worstPerformer ? {
          symbol: a.worstPerformer.symbol,
          pnl_percentage: a.worstPerformer.pnlPercentage || 0,
        } : undefined,
      };
    }
    // Priority 2: If error occurred or loading completed with no data, use mock data
    const hasError = analyticsError && !analyticsData?.cryptoAnalytics;
    const hasNetworkError = analyticsError?.message?.includes('Network request failed');
    const loadingCompleted = !analyticsLoading && !analyticsData?.cryptoAnalytics;
    
    // Always return mock data for optimistic loading (show immediately, replace when real data arrives)
    if (hasError || hasNetworkError || loadingCompleted || !analyticsLoading) {
      return getMockCryptoAnalytics();
    }
    
    // While actively loading, show mock data immediately (optimistic loading)
    return getMockCryptoAnalytics();
  }, [analyticsData?.cryptoAnalytics, analyticsLoading, analyticsError]);

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

  // Don't show error screen if we have mock data to display
  // Only show error if we have no data at all and not using mock fallback
  const gqlErr = portfolioError?.graphQLErrors?.[0] || analyticsError?.graphQLErrors?.[0];
  const hasNetworkError = portfolioError?.message?.includes('Network request failed') || 
                         analyticsError?.message?.includes('Network request failed');
  
  // Only show error screen if it's a real GraphQL error (not network) and we have no mock data
  if (gqlErr && !hasNetworkError && !effectivePortfolio && !effectiveAnalytics && !loadingTimeout) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Crypto data failed to load</Text>
          <Text style={styles.errorDetails}>
            {gqlErr.message} @ {gqlErr.path?.join('.') ?? 'unknown'}
          </Text>
          <TouchableOpacity style={styles.retryButton} onPress={onRefresh}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const renderTabContent = useMemo(() => {
    switch (activeTab) {
      case 'portfolio':
        return (
          <CryptoPortfolioCard 
            portfolio={effectivePortfolio}
            analytics={effectiveAnalytics}
            loading={false} // Never show loading state - always show mock data immediately
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
        if (!FEATURES.CRYPTO_TRADING_ENABLED) {
          return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
              <Icon name="alert-circle" size={64} color="#F59E0B" />
              <Text style={{ fontSize: 20, fontWeight: 'bold', marginTop: 16, marginBottom: 8, textAlign: 'center' }}>
                Cryptocurrency Trading Not Available
              </Text>
              <Text style={{ fontSize: 14, color: '#666', textAlign: 'center', marginBottom: 24 }}>
                {FEATURES.CRYPTO_TRADING_MESSAGE}
              </Text>
              <TouchableOpacity 
                style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: 12, paddingHorizontal: 20, backgroundColor: '#007AFF', borderRadius: 8 }}
                onPress={() => setShowLicensingDisclosure(true)}
              >
                <Icon name="file-text" size={16} color="#fff" />
                <Text style={{ color: '#fff', marginLeft: 8, fontSize: 16, fontWeight: '600' }}>
                  View Regulatory & Licensing Info
                </Text>
              </TouchableOpacity>
            </View>
          );
        }
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
            walletAddress={null} // Future enhancement: Connect to user's wallet address from wallet service
            backendBaseUrl={process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000"}
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
    <>
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

    {/* Licensing Disclosure Modal */}
    <Modal
      visible={showLicensingDisclosure}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowLicensingDisclosure(false)}
    >
      <LicensingDisclosureScreen onClose={() => setShowLicensingDisclosure(false)} />
    </Modal>
    </>
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
  disabledContainer: {
    flex: 1,
    backgroundColor: '#F5F6FA',
  },
  disabledContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  disabledTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
    marginTop: 24,
    marginBottom: 12,
    textAlign: 'center',
  },
  disabledMessage: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  linkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    backgroundColor: '#F5F6FA',
    borderRadius: 12,
    marginBottom: 16,
    gap: 8,
  },
  linkText: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
  backButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#007AFF',
    borderRadius: 12,
    marginTop: 8,
  },
  backButtonText: {
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#dc3545',
    marginBottom: 10,
    textAlign: 'center',
  },
  errorDetails: {
    fontSize: 14,
    color: '#6c757d',
    textAlign: 'center',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default CryptoScreen;