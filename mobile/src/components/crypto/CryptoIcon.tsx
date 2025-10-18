import React from 'react';
import { Image, Text, View, StyleSheet, ImageStyle, TextStyle } from 'react-native';

interface CryptoIconProps {
  symbol: string;
  size?: number;
  style?: ImageStyle;
  fallbackStyle?: TextStyle;
  showFallback?: boolean;
}

const CryptoIcon: React.FC<CryptoIconProps> = ({
  symbol,
  size = 24,
  style,
  fallbackStyle,
  showFallback = true,
}) => {
  const upperSymbol = symbol.toUpperCase();
  
  // CoinGecko API for crypto icons (free, no API key required)
  // We'll construct the URL dynamically based on the coin ID
  
  // Map of common crypto symbols to their CoinGecko image URLs
  const symbolToImageUrl: Record<string, string> = {
    'BTC': 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png',
    'ETH': 'https://assets.coingecko.com/coins/images/279/large/ethereum.png',
    'USDT': 'https://assets.coingecko.com/coins/images/325/large/Tether.png',
    'USDC': 'https://assets.coingecko.com/coins/images/6319/large/USD_Coin_icon.png',
    'BNB': 'https://assets.coingecko.com/coins/images/825/large/bnb-icon2_2x.png',
    'XRP': 'https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png',
    'ADA': 'https://assets.coingecko.com/coins/images/975/large/cardano.png',
    'SOL': 'https://assets.coingecko.com/coins/images/4128/large/solana.png',
    'DOGE': 'https://assets.coingecko.com/coins/images/5/large/dogecoin.png',
    'DOT': 'https://assets.coingecko.com/coins/images/12171/large/polkadot.png',
    'AVAX': 'https://assets.coingecko.com/coins/images/12559/large/Avalanche_Circle_RedWhite_Trans.png',
    'MATIC': 'https://assets.coingecko.com/coins/images/4713/large/matic-token-icon.png',
    'LINK': 'https://assets.coingecko.com/coins/images/877/large/chainlink-new-logo.png',
    'UNI': 'https://assets.coingecko.com/coins/images/12504/large/uni.jpg',
    'LTC': 'https://assets.coingecko.com/coins/images/2/large/litecoin.png',
    'BCH': 'https://assets.coingecko.com/coins/images/780/large/bitcoin-cash.png',
    'ATOM': 'https://assets.coingecko.com/coins/images/1481/large/cosmos_hub.png',
    'XLM': 'https://assets.coingecko.com/coins/images/100/large/Stellar_symbol_black_RGB.png',
    'ALGO': 'https://assets.coingecko.com/coins/images/4030/large/algorand.png',
    'VET': 'https://assets.coingecko.com/coins/images/307/large/vechain.png',
    'ICP': 'https://assets.coingecko.com/coins/images/14495/large/Internet_Computer_logo.png',
    'FIL': 'https://assets.coingecko.com/coins/images/2281/large/filecoin.png',
    'TRX': 'https://assets.coingecko.com/coins/images/1094/large/tron-logo.png',
    'ETC': 'https://assets.coingecko.com/coins/images/453/large/ethereum-classic-logo.png',
    'XMR': 'https://assets.coingecko.com/coins/images/69/large/monero_logo.png',
    'EOS': 'https://assets.coingecko.com/coins/images/738/large/eos-eos-logo.png',
    'AAVE': 'https://assets.coingecko.com/coins/images/12645/large/AAVE.png',
    'SUSHI': 'https://assets.coingecko.com/coins/images/12271/large/512x512_Logo_no_chop.png',
    'COMP': 'https://assets.coingecko.com/coins/images/10775/large/COMP.png',
    'MKR': 'https://assets.coingecko.com/coins/images/1364/large/Mark_Maker.png',
    'YFI': 'https://assets.coingecko.com/coins/images/11849/large/yfi-192x192.png',
    'SNX': 'https://assets.coingecko.com/coins/images/3406/large/SNX.png',
    'UMA': 'https://assets.coingecko.com/coins/images/10927/large/UMA.png',
    'BAL': 'https://assets.coingecko.com/coins/images/11683/large/Balancer.png',
    'CRV': 'https://assets.coingecko.com/coins/images/12124/large/Curve.png',
    '1INCH': 'https://assets.coingecko.com/coins/images/13469/large/1inch.png',
    'SAND': 'https://assets.coingecko.com/coins/images/12129/large/sandbox.png',
    'MANA': 'https://assets.coingecko.com/coins/images/878/large/decentraland-mana.png',
    'ENJ': 'https://assets.coingecko.com/coins/images/1102/large/enjin-coin-logo.png',
    'CHZ': 'https://assets.coingecko.com/coins/images/8834/large/Chiliz.png',
    'BAT': 'https://assets.coingecko.com/coins/images/677/large/basic-attention-token.png',
    'ZRX': 'https://assets.coingecko.com/coins/images/863/large/0x.png',
    'REP': 'https://assets.coingecko.com/coins/images/730/large/REP.png',
    'KNC': 'https://assets.coingecko.com/coins/images/947/large/kyber-network-crystal.png',
    'LRC': 'https://assets.coingecko.com/coins/images/913/large/LRC.png',
    'OMG': 'https://assets.coingecko.com/coins/images/776/large/OMG_Network.jpg',
    'ZIL': 'https://assets.coingecko.com/coins/images/2687/large/zilliqa-logo.png',
    'ONT': 'https://assets.coingecko.com/coins/images/3447/large/ont.jpg',
    'QTUM': 'https://assets.coingecko.com/coins/images/976/large/qtum.png',
    'ICX': 'https://assets.coingecko.com/coins/images/1066/large/icx-icx-logo.png',
    'WAVES': 'https://assets.coingecko.com/coins/images/425/large/waves.png',
    'NEO': 'https://assets.coingecko.com/coins/images/480/large/NEO_512_512.png',
    'DASH': 'https://assets.coingecko.com/coins/images/19/large/dash-logo.png',
    'ZEC': 'https://assets.coingecko.com/coins/images/486/large/circle-zcash.png',
    'DCR': 'https://assets.coingecko.com/coins/images/328/large/decred.png',
    'NANO': 'https://assets.coingecko.com/coins/images/756/large/nano.png',
    'IOTA': 'https://assets.coingecko.com/coins/images/692/large/IOTA_Swirl.png',
    'XTZ': 'https://assets.coingecko.com/coins/images/976/large/Tezos-logo.png',
    'EGLD': 'https://assets.coingecko.com/coins/images/12335/large/elrond3_360.png',
    'HBAR': 'https://assets.coingecko.com/coins/images/2828/large/hbar.png',
    'THETA': 'https://assets.coingecko.com/coins/images/2538/large/theta-token-logo.png',
    'FTM': 'https://assets.coingecko.com/coins/images/4001/large/Fantom_round.png',
    'NEAR': 'https://assets.coingecko.com/coins/images/10365/large/near.jpg',
    'FLOW': 'https://assets.coingecko.com/coins/images/13446/large/5f6294c0c7a8cda55cb1c936_Flow_Wordmark.png',
    'KSM': 'https://assets.coingecko.com/coins/images/9568/large/4Gpwv3X1.png',
    'AR': 'https://assets.coingecko.com/coins/images/12137/large/oJ6S2uqq.png',
    'RUNE': 'https://assets.coingecko.com/coins/images/6592/large/RUNE.png',
    'CAKE': 'https://assets.coingecko.com/coins/images/12632/large/pancakeswap-cake-logo_%281%29.png',
    'BAKE': 'https://assets.coingecko.com/coins/images/12531/large/bakerytoken_logo.jpg',
    'AUTO': 'https://assets.coingecko.com/coins/images/12531/large/bakerytoken_logo.jpg',
    'ALPHA': 'https://assets.coingecko.com/coins/images/12738/large/AlphaToken_256x256.png',
    'BAND': 'https://assets.coingecko.com/coins/images/11682/large/band-protocol.png',
    'REN': 'https://assets.coingecko.com/coins/images/3135/large/REN.png',
    'KAVA': 'https://assets.coingecko.com/coins/images/9763/large/kava.png',
    'ROSE': 'https://assets.coingecko.com/coins/images/14939/large/oasis-network.png',
    'CELO': 'https://assets.coingecko.com/coins/images/11024/large/celo.png',
    'ONE': 'https://assets.coingecko.com/coins/images/4344/large/Y88JAze.png',
    'IOTX': 'https://assets.coingecko.com/coins/images/3334/large/iotex-logo.png',
    'SKL': 'https://assets.coingecko.com/coins/images/10361/large/skale.png',
    'OCEAN': 'https://assets.coingecko.com/coins/images/3687/large/ocean-protocol-logo.jpg',
    'GRT': 'https://assets.coingecko.com/coins/images/14097/large/Graph_Token.png',
    'LPT': 'https://assets.coingecko.com/coins/images/14097/large/Graph_Token.png',
    'STORJ': 'https://assets.coingecko.com/coins/images/1559/large/storj.png',
    'ANKR': 'https://assets.coingecko.com/coins/images/4324/large/ankr.png',
    'RLC': 'https://assets.coingecko.com/coins/images/1631/large/iExec.png',
    'GNO': 'https://assets.coingecko.com/coins/images/662/large/logo_square_simple_300px.png',
    'KEEP': 'https://assets.coingecko.com/coins/images/3373/large/IuNzUb5b_400x400.jpg',
    'NU': 'https://assets.coingecko.com/coins/images/3318/large/photo.png',
  };

  const imageUrl = symbolToImageUrl[upperSymbol];
  
  if (!imageUrl) {
    if (showFallback) {
      return (
        <View style={[styles.fallbackContainer, { width: size, height: size }, style]}>
          <Text style={[styles.fallbackText, { fontSize: size * 0.4 }, fallbackStyle]}>
            {upperSymbol.substring(0, 2)}
          </Text>
        </View>
      );
    }
    return null;
  }

  // Use the direct URL from our mapping
  const finalIconUrl = imageUrl;

  return (
    <Image
      source={{ uri: finalIconUrl }}
      style={[
        styles.icon,
        {
          width: size,
          height: size,
        },
        style,
      ]}
      resizeMode="contain"
      onError={() => {
        // If the image fails to load, we could implement a fallback here
        console.warn(`Failed to load icon for ${upperSymbol}`);
      }}
    />
  );
};

const styles = StyleSheet.create({
  icon: {
    borderRadius: 12,
  },
  fallbackContainer: {
    backgroundColor: '#E5E7EB',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  fallbackText: {
    fontWeight: '600',
    color: '#6B7280',
  },
});

export default CryptoIcon;
