import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';

interface CryptoIconProps {
  symbol: string;
  size?: number;
  iconUrl?: string;
}

const CryptoIcon: React.FC<CryptoIconProps> = ({ symbol, size = 32, iconUrl }) => {
  const upperSymbol = symbol.toUpperCase();
  
  // If we have an iconUrl, we could use it here, but for now let's focus on better fallbacks
  if (iconUrl) {
    // Could implement Image component here if needed
  }

  // Custom crypto symbols for better recognition
  const getCryptoSymbol = (symbol: string) => {
    switch (symbol) {
      case 'BTC':
        return '₿';
      case 'ETH':
        return 'Ξ';
      case 'SOL':
        return '◎';
      case 'ADA':
        return '₳';
      case 'DOT':
        return '●';
      case 'MATIC':
        return '⬟';
      case 'AVAX':
        return '🔺';
      case 'LINK':
        return '🔗';
      case 'UNI':
        return '🦄';
      case 'AAVE':
        return '👻';
      default:
        return symbol.substring(0, 2);
    }
  };

  const getCryptoColor = (symbol: string) => {
    switch (symbol) {
      case 'BTC':
        return '#F7931A'; // Bitcoin orange
      case 'ETH':
        return '#627EEA'; // Ethereum blue
      case 'SOL':
        return '#9945FF'; // Solana purple
      case 'ADA':
        return '#0033AD'; // Cardano blue
      case 'DOT':
        return '#E6007A'; // Polkadot pink
      case 'MATIC':
        return '#8247E5'; // Polygon purple
      case 'AVAX':
        return '#E84142'; // Avalanche red
      case 'LINK':
        return '#2A5ADA'; // Chainlink blue
      case 'UNI':
        return '#FF007A'; // Uniswap pink
      case 'AAVE':
        return '#B6509E'; // Aave purple
      default:
        return '#6B7280'; // Gray for unknown
    }
  };

  const cryptoSymbol = getCryptoSymbol(upperSymbol);
  const cryptoColor = getCryptoColor(upperSymbol);

  return (
    <View style={[styles.container, { width: size, height: size, borderRadius: size / 2 }]}>
      <View style={[styles.iconBackground, { backgroundColor: cryptoColor + '20' }]}>
        <Text style={[styles.iconText, { color: cryptoColor, fontSize: size * 0.5 }]}>
          {cryptoSymbol}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconBackground: {
    width: '100%',
    height: '100%',
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconText: {
    fontWeight: 'bold',
    textAlign: 'center',
  },
});

export default CryptoIcon;
