import React, { useCallback } from 'react';
import { useNavigation } from '@react-navigation/native';
import TradingScreen from '../features/stocks/screens/TradingScreen';

export default function TradingScreenWrapper() {
  const navigation = useNavigation<any>();

  const navigateTo = useCallback((screen: string, params?: any) => {
    // Normalize common routes used by the old navigator
    if (screen === 'home' || screen === 'InvestMain' || screen === 'Invest') {
      navigation.navigate('InvestMain');
      return;
    }
    if (screen === 'Stocks' || screen === 'stock') {
      navigation.navigate('Stocks');
      return;
    }
    if (screen === 'StockDetail' || screen === 'stock-detail') {
      navigation.navigate('StockDetail', params ?? {});
      return;
    }
    navigation.navigate(screen as never, params as never);
  }, [navigation]);

  return <TradingScreen navigateTo={navigateTo} />;
}


