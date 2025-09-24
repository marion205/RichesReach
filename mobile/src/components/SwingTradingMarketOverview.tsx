import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

interface MarketData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: string;
}

interface SectorData {
  name: string;
  symbol: string;
  change: number;
  changePercent: number;
  weight: number;
}

interface VolatilityData {
  vix: number;
  vixChange: number;
  fearGreedIndex: number;
  putCallRatio: number;
}

const SwingTradingMarketOverview: React.FC = () => {
  // Mock data - in real app, this would come from API
  const marketData: MarketData[] = [
    {
      symbol: 'SPY',
      name: 'S&P 500',
      price: 4456.78,
      change: 12.45,
      changePercent: 0.28,
      volume: 45234567,
      marketCap: '$40.2T'
    },
    {
      symbol: 'QQQ',
      name: 'NASDAQ 100',
      price: 3789.23,
      change: -8.92,
      changePercent: -0.23,
      volume: 23456789,
      marketCap: '$15.8T'
    },
    {
      symbol: 'IWM',
      name: 'Russell 2000',
      price: 1892.45,
      change: 5.67,
      changePercent: 0.30,
      volume: 12345678,
      marketCap: '$2.1T'
    },
    {
      symbol: 'VIX',
      name: 'Volatility Index',
      price: 18.45,
      change: -1.23,
      changePercent: -6.25,
      volume: 9876543,
      marketCap: 'N/A'
    }
  ];

  const sectorData: SectorData[] = [
    { name: 'Technology', symbol: 'XLK', change: 0.45, changePercent: 0.32, weight: 28.5 },
    { name: 'Healthcare', symbol: 'XLV', change: -0.12, changePercent: -0.08, weight: 13.2 },
    { name: 'Financials', symbol: 'XLF', change: 0.78, changePercent: 0.56, weight: 11.8 },
    { name: 'Consumer Discretionary', symbol: 'XLY', change: 0.23, changePercent: 0.18, weight: 10.9 },
    { name: 'Communication Services', symbol: 'XLC', change: -0.34, changePercent: -0.25, weight: 8.7 },
    { name: 'Industrials', symbol: 'XLI', change: 0.67, changePercent: 0.48, weight: 8.1 },
    { name: 'Consumer Staples', symbol: 'XLP', change: 0.15, changePercent: 0.12, weight: 6.8 },
    { name: 'Energy', symbol: 'XLE', change: 1.23, changePercent: 0.89, weight: 4.2 },
    { name: 'Utilities', symbol: 'XLU', change: -0.08, changePercent: -0.06, weight: 3.1 },
    { name: 'Real Estate', symbol: 'XLRE', change: 0.34, changePercent: 0.28, weight: 2.8 },
    { name: 'Materials', symbol: 'XLB', change: 0.56, changePercent: 0.42, weight: 2.0 }
  ];

  const volatilityData: VolatilityData = {
    vix: 18.45,
    vixChange: -1.23,
    fearGreedIndex: 65,
    putCallRatio: 0.78
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return '#10B981';
    if (change < 0) return '#EF4444';
    return '#6B7280';
  };

  const getFearGreedColor = (index: number) => {
    if (index >= 75) return '#EF4444'; // Extreme Greed
    if (index >= 55) return '#F59E0B'; // Greed
    if (index >= 45) return '#10B981'; // Neutral
    if (index >= 25) return '#F59E0B'; // Fear
    return '#EF4444'; // Extreme Fear
  };

  const getFearGreedLabel = (index: number) => {
    if (index >= 75) return 'Extreme Greed';
    if (index >= 55) return 'Greed';
    if (index >= 45) return 'Neutral';
    if (index >= 25) return 'Fear';
    return 'Extreme Fear';
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`;
    return volume.toString();
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Market Indices */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="trending-up" size={20} color="#3B82F6" />
          <Text style={styles.sectionTitle}>Market Indices</Text>
          <Text style={styles.sectionSubtitle}>Live Market Data</Text>
        </View>
        
        <View style={styles.marketGrid}>
          {marketData.map((market, index) => (
            <View key={index} style={styles.marketCard}>
              <View style={styles.marketHeader}>
                <Text style={styles.marketSymbol}>{market.symbol}</Text>
                <Text style={styles.marketName}>{market.name}</Text>
              </View>
              <Text style={styles.marketPrice}>${market.price.toFixed(2)}</Text>
              <View style={styles.marketChange}>
                <Text style={[styles.changeText, { color: getChangeColor(market.change) }]}>
                  {market.change > 0 ? '+' : ''}{market.change.toFixed(2)} ({market.changePercent > 0 ? '+' : ''}{market.changePercent.toFixed(2)}%)
                </Text>
              </View>
              <View style={styles.marketFooter}>
                <Text style={styles.volumeText}>Vol: {formatVolume(market.volume)}</Text>
                <Text style={styles.marketCapText}>{market.marketCap}</Text>
              </View>
            </View>
          ))}
        </View>
      </View>

      {/* Sector Performance */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="layers" size={20} color="#10B981" />
          <Text style={styles.sectionTitle}>Sector Performance</Text>
          <Text style={styles.sectionSubtitle}>Today's Sector Rotation</Text>
        </View>
        
        <View style={styles.sectorList}>
          {sectorData.map((sector, index) => (
            <TouchableOpacity key={index} style={styles.sectorItem}>
              <View style={styles.sectorInfo}>
                <Text style={styles.sectorName}>{sector.name}</Text>
                <Text style={styles.sectorSymbol}>{sector.symbol}</Text>
              </View>
              <View style={styles.sectorMetrics}>
                <Text style={styles.sectorWeight}>{sector.weight.toFixed(1)}%</Text>
                <Text style={[styles.sectorChange, { color: getChangeColor(sector.change) }]}>
                  {sector.change > 0 ? '+' : ''}{sector.changePercent.toFixed(2)}%
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Market Sentiment */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="activity" size={20} color="#F59E0B" />
          <Text style={styles.sectionTitle}>Market Sentiment</Text>
          <Text style={styles.sectionSubtitle}>Fear & Greed Indicators</Text>
        </View>
        
        <View style={styles.sentimentGrid}>
          <View style={styles.sentimentCard}>
            <View style={styles.sentimentHeader}>
              <Text style={styles.sentimentTitle}>VIX</Text>
              <Text style={styles.sentimentSubtitle}>Volatility Index</Text>
            </View>
            <Text style={styles.sentimentValue}>{volatilityData.vix.toFixed(2)}</Text>
            <Text style={[styles.sentimentChange, { color: getChangeColor(volatilityData.vixChange) }]}>
              {volatilityData.vixChange > 0 ? '+' : ''}{volatilityData.vixChange.toFixed(2)}
            </Text>
          </View>

          <View style={styles.sentimentCard}>
            <View style={styles.sentimentHeader}>
              <Text style={styles.sentimentTitle}>Fear & Greed</Text>
              <Text style={styles.sentimentSubtitle}>Market Sentiment</Text>
            </View>
            <Text style={[styles.sentimentValue, { color: getFearGreedColor(volatilityData.fearGreedIndex) }]}>
              {volatilityData.fearGreedIndex}
            </Text>
            <Text style={[styles.sentimentLabel, { color: getFearGreedColor(volatilityData.fearGreedIndex) }]}>
              {getFearGreedLabel(volatilityData.fearGreedIndex)}
            </Text>
          </View>

          <View style={styles.sentimentCard}>
            <View style={styles.sentimentHeader}>
              <Text style={styles.sentimentTitle}>Put/Call Ratio</Text>
              <Text style={styles.sentimentSubtitle}>Options Sentiment</Text>
            </View>
            <Text style={styles.sentimentValue}>{volatilityData.putCallRatio.toFixed(2)}</Text>
            <Text style={styles.sentimentLabel}>
              {volatilityData.putCallRatio > 1 ? 'Bearish' : volatilityData.putCallRatio < 0.7 ? 'Bullish' : 'Neutral'}
            </Text>
          </View>
        </View>
      </View>

      {/* Market Breadth */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="bar-chart" size={20} color="#8B5CF6" />
          <Text style={styles.sectionTitle}>Market Breadth</Text>
          <Text style={styles.sectionSubtitle}>Advance/Decline Analysis</Text>
        </View>
        
        <View style={styles.breadthGrid}>
          <View style={styles.breadthCard}>
            <Text style={styles.breadthTitle}>NYSE</Text>
            <View style={styles.breadthStats}>
              <View style={styles.breadthStat}>
                <Text style={styles.breadthNumber}>2,847</Text>
                <Text style={styles.breadthLabel}>Advancing</Text>
              </View>
              <View style={styles.breadthStat}>
                <Text style={styles.breadthNumber}>1,234</Text>
                <Text style={styles.breadthLabel}>Declining</Text>
              </View>
            </View>
            <Text style={[styles.breadthRatio, { color: '#10B981' }]}>2.31:1</Text>
          </View>

          <View style={styles.breadthCard}>
            <Text style={styles.breadthTitle}>NASDAQ</Text>
            <View style={styles.breadthStats}>
              <View style={styles.breadthStat}>
                <Text style={styles.breadthNumber}>1,892</Text>
                <Text style={styles.breadthLabel}>Advancing</Text>
              </View>
              <View style={styles.breadthStat}>
                <Text style={styles.breadthNumber}>1,456</Text>
                <Text style={styles.breadthLabel}>Declining</Text>
              </View>
            </View>
            <Text style={[styles.breadthRatio, { color: '#10B981' }]}>1.30:1</Text>
          </View>
        </View>
      </View>

      {/* Economic Calendar Preview */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="calendar" size={20} color="#EC4899" />
          <Text style={styles.sectionTitle}>Economic Calendar</Text>
          <Text style={styles.sectionSubtitle}>Upcoming Events</Text>
        </View>
        
        <View style={styles.economicList}>
          <View style={styles.economicItem}>
            <View style={styles.economicTime}>
              <Text style={styles.economicDate}>Today</Text>
              <Text style={styles.economicHour}>10:00 AM</Text>
            </View>
            <View style={styles.economicInfo}>
              <Text style={styles.economicEvent}>CPI Data</Text>
              <Text style={styles.economicImpact}>High Impact</Text>
            </View>
            <View style={[styles.impactBadge, { backgroundColor: '#EF4444' }]}>
              <Text style={styles.impactText}>HIGH</Text>
            </View>
          </View>

          <View style={styles.economicItem}>
            <View style={styles.economicTime}>
              <Text style={styles.economicDate}>Tomorrow</Text>
              <Text style={styles.economicHour}>2:00 PM</Text>
            </View>
            <View style={styles.economicInfo}>
              <Text style={styles.economicEvent}>FOMC Meeting</Text>
              <Text style={styles.economicImpact}>Medium Impact</Text>
            </View>
            <View style={[styles.impactBadge, { backgroundColor: '#F59E0B' }]}>
              <Text style={styles.impactText}>MED</Text>
            </View>
          </View>

          <View style={styles.economicItem}>
            <View style={styles.economicTime}>
              <Text style={styles.economicDate}>Friday</Text>
              <Text style={styles.economicHour}>8:30 AM</Text>
            </View>
            <View style={styles.economicInfo}>
              <Text style={styles.economicEvent}>Jobs Report</Text>
              <Text style={styles.economicImpact}>High Impact</Text>
            </View>
            <View style={[styles.impactBadge, { backgroundColor: '#EF4444' }]}>
              <Text style={styles.impactText}>HIGH</Text>
            </View>
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  section: {
    marginBottom: 24,
    paddingHorizontal: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginLeft: 8,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 'auto',
  },
  marketGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  marketCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    width: (width - 48) / 2,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  marketHeader: {
    marginBottom: 8,
  },
  marketSymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  marketName: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  marketPrice: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  marketChange: {
    marginBottom: 8,
  },
  changeText: {
    fontSize: 14,
    fontWeight: '600',
  },
  marketFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  volumeText: {
    fontSize: 11,
    color: '#6B7280',
  },
  marketCapText: {
    fontSize: 11,
    color: '#6B7280',
  },
  sectorList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  sectorItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  sectorInfo: {
    flex: 1,
  },
  sectorName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  sectorSymbol: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  sectorMetrics: {
    alignItems: 'flex-end',
  },
  sectorWeight: {
    fontSize: 12,
    color: '#6B7280',
  },
  sectorChange: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 2,
  },
  sentimentGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  sentimentCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    width: (width - 48) / 3,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  sentimentHeader: {
    marginBottom: 8,
  },
  sentimentTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  sentimentSubtitle: {
    fontSize: 10,
    color: '#6B7280',
    marginTop: 2,
  },
  sentimentValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  sentimentChange: {
    fontSize: 12,
    fontWeight: '600',
  },
  sentimentLabel: {
    fontSize: 10,
    fontWeight: '600',
  },
  breadthGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  breadthCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    width: (width - 48) / 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  breadthTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
    textAlign: 'center',
  },
  breadthStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  breadthStat: {
    alignItems: 'center',
  },
  breadthNumber: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  breadthLabel: {
    fontSize: 10,
    color: '#6B7280',
    marginTop: 2,
  },
  breadthRatio: {
    fontSize: 14,
    fontWeight: '700',
    textAlign: 'center',
  },
  economicList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  economicItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  economicTime: {
    width: 80,
    marginRight: 12,
  },
  economicDate: {
    fontSize: 12,
    fontWeight: '600',
    color: '#111827',
  },
  economicHour: {
    fontSize: 10,
    color: '#6B7280',
    marginTop: 2,
  },
  economicInfo: {
    flex: 1,
  },
  economicEvent: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  economicImpact: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  impactBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  impactText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});

export default SwingTradingMarketOverview;
