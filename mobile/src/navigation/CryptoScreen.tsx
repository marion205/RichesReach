/**
 * Crypto Trading Screen
 * Main screen for crypto trading functionality
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

// Components
import ProAaveCard from '../components/forms/ProAaveCard';
import CryptoPortfolioCard from '../components/crypto/CryptoPortfolioCard';
import CryptoTradingCardPro from '../components/crypto/CryptoTradingCardPro';
import CryptoMLSignalsCard from '../components/crypto/CryptoMLSignalsCard';

interface CryptoScreenProps {
  navigation: any;
}

const CryptoScreen: React.FC<CryptoScreenProps> = ({ navigation }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'portfolio' | 'trading' | 'aave' | 'signals'>('aave');
  const [hideBalances, setHideBalances] = useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    // Simulate refresh delay
    setTimeout(() => {
      setRefreshing(false);
    }, 1000);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'portfolio':
        return (
          <CryptoPortfolioCard 
            portfolio={{
              total_value_usd: 12547.50,
              total_pnl: 1247.50,
              total_pnl_percentage: 11.05,
              total_pnl_1d: 125.30,
              total_pnl_pct_1d: 1.01,
              total_pnl_1w: 847.20,
              total_pnl_pct_1w: 7.25,
              total_pnl_1m: 1247.50,
              total_pnl_pct_1m: 11.05,
              holdings: [
                {
                  cryptocurrency: { symbol: 'BTC' },
                  quantity: 0.25,
                  current_value: 8750.00,
                  unrealized_pnl_percentage: 8.5
                },
                {
                  cryptocurrency: { symbol: 'ETH' },
                  quantity: 2.5,
                  current_value: 2897.50,
                  unrealized_pnl_percentage: 12.3
                },
                {
                  cryptocurrency: { symbol: 'SOL' },
                  quantity: 15.0,
                  current_value: 900.00,
                  unrealized_pnl_percentage: -2.1
                }
              ]
            }}
            analytics={{
              portfolio_volatility: 0.15,
              sharpe_ratio: 1.8,
              max_drawdown: 8.2,
              diversification_score: 75,
              sector_allocation: {
                'LOW': 25,
                'MEDIUM': 40,
                'HIGH': 35
              },
              best_performer: { symbol: 'ETH', pnl_percentage: 12.3 },
              worst_performer: { symbol: 'SOL', pnl_percentage: -2.1 }
            }}
            loading={false}
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
            backendBaseUrl="http://127.0.0.1:8000" // Your backend URL
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
      default:
        return null;
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Crypto DeFi</Text>
        <TouchableOpacity onPress={() => setHideBalances(!hideBalances)} style={styles.hideButton}>
          <Icon name={hideBalances ? 'eye-off' : 'eye'} size={20} color="#fff" />
        </TouchableOpacity>
      </View>

      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'portfolio' && styles.activeTab]}
          onPress={() => setActiveTab('portfolio')}
        >
          <Icon name="pie-chart" size={16} color={activeTab === 'portfolio' ? '#007bff' : '#6c757d'} />
          <Text style={[styles.tabText, activeTab === 'portfolio' && styles.activeTabText]}>Portfolio</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'trading' && styles.activeTab]}
          onPress={() => setActiveTab('trading')}
        >
          <Icon name="trending-up" size={16} color={activeTab === 'trading' ? '#007bff' : '#6c757d'} />
          <Text style={[styles.tabText, activeTab === 'trading' && styles.activeTabText]}>Trading</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'aave' && styles.activeTab]}
          onPress={() => setActiveTab('aave')}
        >
          <Icon name="activity" size={16} color={activeTab === 'aave' ? '#007bff' : '#6c757d'} />
          <Text style={[styles.tabText, activeTab === 'aave' && styles.activeTabText]}>AAVE</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'signals' && styles.activeTab]}
          onPress={() => setActiveTab('signals')}
        >
          <Icon name="activity" size={16} color={activeTab === 'signals' ? '#007bff' : '#6c757d'} />
          <Text style={[styles.tabText, activeTab === 'signals' && styles.activeTabText]}>Signals</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.contentContainer}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {renderTabContent()}
      </ScrollView>
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
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#e9ecef',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#dee2e6',
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 20,
  },
  activeTab: {
    backgroundColor: '#e7f1ff',
  },
  tabText: {
    marginLeft: 5,
    fontSize: 14,
    fontWeight: '600',
    color: '#6c757d',
  },
  activeTabText: {
    color: '#007bff',
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