import React, { useState, useEffect } from 'react';
import { View, StyleSheet, SafeAreaView, Alert } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useQuery } from '@apollo/client';
import { GET_MY_PORTFOLIOS } from '../../../portfolioQueries';
import WellnessScoreDashboard from '../../../components/WellnessScoreDashboard';

export default function WellnessDashboardScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  
  // Get portfolio data from route params or fetch it
  const { data: portfolioData } = useQuery(GET_MY_PORTFOLIOS, {
    errorPolicy: 'all',
    fetchPolicy: 'cache-first',
  });

  // Get portfolio from route params or use the first portfolio from query
  const routePortfolio = route?.params?.portfolio;
  const queryPortfolios = portfolioData?.myPortfolios?.portfolios || [];
  const firstPortfolio = queryPortfolios.length > 0 ? queryPortfolios[0] : null;
  
  // Use route portfolio, first query portfolio, or create demo portfolio
  const portfolio = routePortfolio || firstPortfolio || {
    name: 'Main Portfolio',
    totalValue: 14303.52,
    holdingsCount: 3,
    holdings: [
      { id: 'h1', stock: { symbol: 'AAPL' }, shares: 10, averagePrice: 150, currentPrice: 180, totalValue: 1800 },
      { id: 'h2', stock: { symbol: 'MSFT' }, shares: 8, averagePrice: 230, currentPrice: 320, totalValue: 2560 },
      { id: 'h3', stock: { symbol: 'SPY' }, shares: 15, averagePrice: 380, currentPrice: 420, totalValue: 6300 },
    ],
  };

  const handleClose = () => {
    navigation.goBack();
  };

  const handleActionPress = (action: string) => {
    console.log(`Wellness Action: ${action}`, portfolio);
    
    switch (action) {
      case 'Auto-Rebalance':
        Alert.alert(
          'Auto-Rebalance Portfolio',
          'This will automatically rebalance your portfolio to match your target allocation. Would you like to continue?',
          [
            { text: 'Cancel', style: 'cancel' },
            { 
              text: 'Continue', 
              onPress: () => {
                // Navigate to portfolio screen with rebalance option
                navigation.navigate('Invest', { 
                  screen: 'Portfolio',
                  params: { action: 'rebalance', portfolio }
                });
              }
            }
          ]
        );
        break;
      case 'Tax Harvest':
        Alert.alert(
          'Tax Loss Harvesting',
          'This will identify and execute tax-loss harvesting opportunities in your portfolio to optimize your tax situation.',
          [
            { text: 'Cancel', style: 'cancel' },
            { 
              text: 'View Opportunities', 
              onPress: () => {
                // Navigate to portfolio with tax harvest option
                navigation.navigate('Invest', { 
                  screen: 'Portfolio',
                  params: { action: 'tax-harvest', portfolio }
                });
              }
            }
          ]
        );
        break;
      case 'Risk Adjust':
        // Navigate directly to risk management screen
        navigation.navigate('Invest', { 
          screen: 'RiskManagement',
          params: { portfolio }
        });
        break;
      case 'AI Optimize':
        // Navigate to AI portfolio optimization
        navigation.navigate('Invest', { 
          screen: 'AIPortfolio',
          params: { portfolio }
        });
        break;
      default:
        // Fallback - show alert
        Alert.alert('Action', `The ${action} feature is coming soon!`);
        console.log('Unhandled action:', action);
        break;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <WellnessScoreDashboard
        portfolio={portfolio}
        onClose={handleClose}
        onActionPress={handleActionPress}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
});

