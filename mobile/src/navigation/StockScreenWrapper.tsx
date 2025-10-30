import React, { useCallback } from 'react';
import { useNavigation } from '@react-navigation/native';
import StockScreen from '../features/stocks/screens/StockScreen';

export default function StockScreenWrapper() {
  const navigation = useNavigation<any>();

  const navigateTo = useCallback((screen: string, params?: any) => {
    if (screen === 'StockDetail' || screen === 'stock-detail') {
      navigation.navigate('StockDetail', params ?? {});
      return;
    }
    if (screen === 'stock' || screen === 'Stocks') {
      navigation.navigate('Stocks');
      return;
    }
    // Fallback to generic navigate for other routes within Invest
    navigation.navigate(screen as never, params as never);
  }, [navigation]);

  return <StockScreen navigateTo={navigateTo} />;
}


