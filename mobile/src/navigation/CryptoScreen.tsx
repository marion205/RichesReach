/**
 * Crypto Trading Screen
 * Main screen for crypto trading functionality
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

// Helper function for formatting
const fmt = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);

// GraphQL queries
import { GET_CRYPTO_PORTFOLIO, GET_CRYPTO_ANALYTICS, REPAY_SBLOC_LOAN } from '../cryptoQueries';
import { gql } from '@apollo/client';

const GET_CRYPTO_SBLOC_LOANS = gql`
  query GetCryptoSblocLoans {
    cryptoSblocLoans {
      id
      status
      collateralQuantity
      loanAmount
      interestRate
      cryptocurrency {
        symbol
      }
    }
  }
`;

const GET_CRYPTO_PRICES = gql`
  query GetCryptoPrices($symbols: [String!]!) {
    cryptoPrices(symbols: $symbols) {
      symbol
      priceUsd
    }
  }
`;

// Components
import CryptoPortfolioCard from '../components/crypto/CryptoPortfolioCard';
import CryptoMLSignalsCard from '../components/crypto/CryptoMLSignalsCard';
import CryptoRecommendationsCard from '../components/crypto/CryptoRecommendationsCard';
import CryptoTradingCard from '../components/crypto/CryptoTradingCard';
import CryptoSBLOCCard from '../components/crypto/CryptoSBLOCCard';
import CollateralHealthCard from '../components/crypto/CollateralHealthCard';
import LoanManagementModal from '../components/crypto/LoanManagementModal';

interface CryptoScreenProps {
  navigation: any;
}

const CryptoScreen: React.FC<CryptoScreenProps> = ({ navigation }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'portfolio' | 'trading' | 'sbloc' | 'signals'>('portfolio');
  const [hideBalances, setHideBalances] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<string | null>(null);

  // GraphQL queries
  const { 
    data: portfolioData, 
    loading: portfolioLoading, 
    refetch: refetchPortfolio 
  } = useQuery(GET_CRYPTO_PORTFOLIO);

  const { 
    data: analyticsData, 
    loading: analyticsLoading, 
    refetch: refetchAnalytics 
  } = useQuery(GET_CRYPTO_ANALYTICS);

  const { data: loansData } = useQuery(GET_CRYPTO_SBLOC_LOANS);
  
  // Get unique symbols from loans for price lookup
  const loanSymbols = loansData?.cryptoSblocLoans?.map((loan: any) => loan.cryptocurrency.symbol) || [];
  const { data: pricesData } = useQuery(GET_CRYPTO_PRICES, {
    variables: { symbols: loanSymbols },
    skip: loanSymbols.length === 0,
  });

  // Repay SBLOC loan mutation
  const [repaySblocLoan, { loading: repaying }] = useMutation(REPAY_SBLOC_LOAN, {
    onError: (e) => console.error('Repay error:', e),
  });

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refetchPortfolio(),
        refetchAnalytics(),
      ]);
    } catch (error) {
      console.error('Error refreshing crypto data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleAssetPress = (symbol: string) => {
    setSelectedAsset(symbol);
    setModalVisible(true);
  };

  const handleAddCollateral = (loanId: string, symbol: string) => {
    setModalVisible(false);
    setActiveTab('sbloc');
    Alert.alert('Add Collateral', `Navigate to SBLOC tab to add more ${symbol} as collateral for loan ${loanId}`);
  };

  const handleRepayConfirm = async (loanId: string, symbol: string, amountUsd: number) => {
    try {
      const { data } = await repaySblocLoan({
        variables: { loanId, amountUsd },
        // Make sure the loan list & portfolio refresh
        refetchQueries: ['GetCryptoSblocLoans', 'GetCryptoPortfolio', 'GetCryptoAnalytics'],
        awaitRefetchQueries: true,
      });

      const res = data?.repaySblocLoan;
      if (!res?.success) {
        Alert.alert('Repay Failed', res?.message ?? 'Please try again.');
        return;
      }

      Alert.alert(
        'Repayment Successful',
        `Paid ${fmt(res.interestPaid + res.principalPaid)}\n` +
        `• Interest: ${fmt(res.interestPaid)}\n` +
        `• Principal: ${fmt(res.principalPaid)}\n` +
        `New Outstanding: ${fmt(res.newOutstanding)}`
      );
      
      setModalVisible(false);
    } catch (err) {
      console.error('Repay error:', err);
      Alert.alert('Error', 'Could not process repayment.');
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'portfolio':
        // Build priceMap for collateral health
        const priceMap = Object.fromEntries(
          (pricesData?.cryptoPrices ?? []).map((p: any) => [p.symbol, p.priceUsd])
        );

        // Compute portfolio LTV state for portfolio card
        const { portfolioLtv, ltvState } = (() => {
          const active = (loansData?.cryptoSblocLoans ?? []).filter((l:any) => ['ACTIVE','WARNING'].includes(l.status));
          let collat = 0, loans = 0;
          active.forEach((l:any) => {
            const px = priceMap[l.cryptocurrency.symbol] || 0;
            collat += parseFloat(l.collateralQuantity || 0) * px;
            loans  += parseFloat(l.loanAmount || 0);
          });
          const ltv = collat > 0 ? (loans / collat) * 100 : 0;
          const state = ltv <= 35 ? 'SAFE' : ltv <= 40 ? 'CAUTION' : ltv <= 50 ? 'AT_RISK' : 'DANGER';
          return { portfolioLtv: ltv, ltvState: state as 'SAFE'|'CAUTION'|'AT_RISK'|'DANGER' };
        })();

        return (
          <View>
            <CryptoPortfolioCard
              portfolio={portfolioData?.cryptoPortfolio}
              analytics={analyticsData?.cryptoAnalytics}
              loading={portfolioLoading || analyticsLoading}
              onRefresh={onRefresh}
              onPressHolding={(symbol) => {
                // Navigate to holding details or show modal
                Alert.alert('Holding Details', `View details for ${symbol}`);
              }}
              onStartTrading={() => setActiveTab('trading')}
              hideBalances={hideBalances}
              onToggleHideBalances={setHideBalances}
              ltvState={ltvState}
            />
            <CollateralHealthCard 
              loans={loansData?.cryptoSblocLoans ?? []} 
              priceMap={priceMap}
              onAssetPress={handleAssetPress}
            />
          </View>
        );
      case 'trading':
        return (
          <CryptoTradingCard
            onTradeSuccess={() => {
              refetchPortfolio();
              refetchAnalytics();
            }}
          />
        );
      case 'sbloc':
        return (
          <CryptoSBLOCCard
            onLoanSuccess={() => {
              refetchPortfolio();
              refetchAnalytics();
            }}
            onTopUpCollateral={(symbol) => {
              // Navigate to trading tab with pre-selected symbol
              setActiveTab('trading');
              Alert.alert('Top-up Collateral', `Navigate to trading to buy more ${symbol}`);
            }}
          />
        );
      case 'signals':
        return (
          <View>
            <CryptoMLSignalsCard pollInterval={60_000} />
            <CryptoRecommendationsCard 
              onRecommendationPress={(symbol) => {
                setActiveTab('trading');
                Alert.alert('Trading', `Navigate to trading to buy ${symbol}`);
              }}
              maxRecommendations={5}
            />
          </View>
        );
      default:
        return null;
    }
  };

  const renderTabButton = (tab: string, label: string, icon: string) => (
    <TouchableOpacity
      key={tab}
      style={[
        styles.tabButton,
        activeTab === tab && styles.activeTabButton
      ]}
      onPress={() => setActiveTab(tab as any)}
    >
      <Icon 
        name={icon} 
        size={20} 
        color={activeTab === tab ? '#007AFF' : '#8E8E93'} 
      />
      <Text style={[
        styles.tabButtonText,
        activeTab === tab && styles.activeTabButtonText
      ]}>
        {label}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Crypto Trading</Text>
        <TouchableOpacity
          style={styles.headerButton}
          onPress={() => navigation.navigate('CryptoEducation')}
        >
          <Icon name="book-open" size={24} color="#007AFF" />
        </TouchableOpacity>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        {renderTabButton('portfolio', 'Portfolio', 'pie-chart')}
        {renderTabButton('trading', 'Trade', 'trending-up')}
        {renderTabButton('sbloc', 'SBLOC', 'credit-card')}
        {renderTabButton('signals', 'Signals', 'zap')}
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#007AFF"
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {renderTabContent()}
      </ScrollView>

      {/* Loan Management Modal */}
      <LoanManagementModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        symbol={selectedAsset}
        loans={loansData?.cryptoSblocLoans ?? []}
        onAddCollateral={handleAddCollateral}
        onRepayConfirm={handleRepayConfirm}
        isRepaying={repaying}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
  },
  headerButton: {
    padding: 8,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
    marginHorizontal: 4,
  },
  activeTabButton: {
    backgroundColor: '#EFF6FF',
  },
  tabButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
    marginLeft: 6,
  },
  activeTabButtonText: {
    color: '#007AFF',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
});

export default CryptoScreen;
