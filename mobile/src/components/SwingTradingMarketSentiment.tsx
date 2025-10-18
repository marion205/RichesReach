import React, { useState } from 'react';
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

interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  timestamp: string;
  impact: 'high' | 'medium' | 'low';
  sentiment: 'bullish' | 'bearish' | 'neutral';
  relatedSymbols: string[];
  category: string;
}

interface EconomicEvent {
  id: string;
  event: string;
  time: string;
  impact: 'high' | 'medium' | 'low';
  previous: string;
  forecast: string;
  actual?: string;
  description: string;
}

interface SentimentIndicator {
  name: string;
  value: number;
  change: number;
  description: string;
  level: 'extreme' | 'high' | 'moderate' | 'low';
}

const SwingTradingMarketSentiment: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState('news');

  const sentimentIndicators: SentimentIndicator[] = [
    {
      name: 'Fear & Greed Index',
      value: 65,
      change: 5,
      description: 'Market sentiment based on multiple indicators',
      level: 'moderate'
    },
    {
      name: 'Put/Call Ratio',
      value: 0.78,
      change: -0.12,
      description: 'Options sentiment indicator',
      level: 'moderate'
    },
    {
      name: 'VIX',
      value: 18.5,
      change: -1.2,
      description: 'Volatility index',
      level: 'low'
    },
    {
      name: 'AAII Sentiment',
      value: 42,
      change: 8,
      description: 'Individual investor sentiment',
      level: 'moderate'
    },
    {
      name: 'Insider Trading',
      value: -0.3,
      change: -0.1,
      description: 'Net insider selling (negative = selling)',
      level: 'moderate'
    },
    {
      name: 'Margin Debt',
      value: 850.2,
      change: 12.5,
      description: 'Total margin debt (billions)',
      level: 'high'
    }
  ];

  const newsItems: NewsItem[] = [
    {
      id: '1',
      title: 'Fed Signals Potential Rate Cuts as Inflation Cools',
      summary: 'Federal Reserve officials hint at possible interest rate reductions in the coming months as inflation data shows continued moderation.',
      source: 'Reuters',
      timestamp: '2 hours ago',
      impact: 'high',
      sentiment: 'bullish',
      relatedSymbols: ['SPY', 'QQQ', 'TLT'],
      category: 'Monetary Policy'
    },
    {
      id: '2',
      title: 'Tech Earnings Beat Expectations, AI Revenue Surges',
      summary: 'Major technology companies report stronger-than-expected earnings with artificial intelligence revenue showing significant growth.',
      source: 'Bloomberg',
      timestamp: '4 hours ago',
      impact: 'high',
      sentiment: 'bullish',
      relatedSymbols: ['NVDA', 'MSFT', 'GOOGL', 'META'],
      category: 'Earnings'
    },
    {
      id: '3',
      title: 'Energy Sector Faces Headwinds as Oil Prices Decline',
      summary: 'Crude oil prices drop 3% on concerns over global demand and increased supply from non-OPEC producers.',
      source: 'CNBC',
      timestamp: '6 hours ago',
      impact: 'medium',
      sentiment: 'bearish',
      relatedSymbols: ['XLE', 'XOM', 'CVX', 'COP'],
      category: 'Commodities'
    },
    {
      id: '4',
      title: 'Housing Market Shows Signs of Recovery',
      summary: 'New home sales data indicates a potential turnaround in the housing market with mortgage rates stabilizing.',
      source: 'MarketWatch',
      timestamp: '8 hours ago',
      impact: 'medium',
      sentiment: 'bullish',
      relatedSymbols: ['XHB', 'LEN', 'DHI', 'PHM'],
      category: 'Economic Data'
    },
    {
      id: '5',
      title: 'Cryptocurrency Market Sees Increased Institutional Adoption',
      summary: 'Several major corporations announce Bitcoin treasury allocations, driving crypto market optimism.',
      source: 'CoinDesk',
      timestamp: '12 hours ago',
      impact: 'low',
      sentiment: 'bullish',
      relatedSymbols: ['BTC', 'ETH', 'COIN', 'MSTR'],
      category: 'Cryptocurrency'
    }
  ];

  const economicEvents: EconomicEvent[] = [
    {
      id: '1',
      event: 'CPI (Consumer Price Index)',
      time: 'Today 8:30 AM',
      impact: 'high',
      previous: '3.2%',
      forecast: '3.1%',
      actual: '3.0%',
      description: 'Monthly inflation data showing price changes for consumer goods and services'
    },
    {
      id: '2',
      event: 'FOMC Meeting Minutes',
      time: 'Tomorrow 2:00 PM',
      impact: 'high',
      previous: 'N/A',
      forecast: 'N/A',
      description: 'Detailed minutes from the latest Federal Open Market Committee meeting'
    },
    {
      id: '3',
      event: 'Non-Farm Payrolls',
      time: 'Friday 8:30 AM',
      impact: 'high',
      previous: '175K',
      forecast: '180K',
      description: 'Monthly employment report showing job creation in the US economy'
    },
    {
      id: '4',
      event: 'Retail Sales',
      time: 'Monday 8:30 AM',
      impact: 'medium',
      previous: '0.7%',
      forecast: '0.5%',
      description: 'Monthly retail sales data indicating consumer spending trends'
    },
    {
      id: '5',
      event: 'GDP Growth Rate',
      time: 'Wednesday 8:30 AM',
      impact: 'medium',
      previous: '2.1%',
      forecast: '2.3%',
      description: 'Quarterly economic growth rate for the United States'
    }
  ];

  const tabs = [
    { key: 'news', label: 'Market News', icon: 'newspaper' },
    { key: 'events', label: 'Economic Events', icon: 'calendar' },
    { key: 'sentiment', label: 'Sentiment', icon: 'activity' }
  ];

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return '#EF4444';
      case 'medium': return '#F59E0B';
      case 'low': return '#10B981';
      default: return '#6B7280';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return '#10B981';
      case 'bearish': return '#EF4444';
      case 'neutral': return '#6B7280';
      default: return '#6B7280';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return 'trending-up';
      case 'bearish': return 'trending-down';
      case 'neutral': return 'minus';
      default: return 'minus';
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'extreme': return '#EF4444';
      case 'high': return '#F59E0B';
      case 'moderate': return '#10B981';
      case 'low': return '#3B82F6';
      default: return '#6B7280';
    }
  };

  const renderNews = () => (
    <View style={styles.content}>
      {newsItems.map((news) => (
        <View key={news.id} style={styles.newsCard}>
          <View style={styles.newsHeader}>
            <View style={styles.newsMeta}>
              <Text style={styles.newsSource}>{news.source}</Text>
              <Text style={styles.newsTime}>{news.timestamp}</Text>
            </View>
            <View style={styles.newsBadges}>
              <View style={[styles.impactBadge, { backgroundColor: getImpactColor(news.impact) }]}>
                <Text style={styles.badgeText}>{news.impact.toUpperCase()}</Text>
              </View>
              <View style={[styles.sentimentBadge, { backgroundColor: getSentimentColor(news.sentiment) }]}>
                <Icon name={getSentimentIcon(news.sentiment)} size={12} color="#FFFFFF" />
                <Text style={styles.badgeText}>{news.sentiment.toUpperCase()}</Text>
              </View>
            </View>
          </View>
          
          <Text style={styles.newsTitle}>{news.title}</Text>
          <Text style={styles.newsSummary}>{news.summary}</Text>
          
          <View style={styles.newsFooter}>
            <View style={styles.newsCategory}>
              <Icon name="tag" size={12} color="#6B7280" />
              <Text style={styles.categoryText}>{news.category}</Text>
            </View>
            {news.relatedSymbols && news.relatedSymbols.length > 0 && (
              <View style={styles.relatedSymbols}>
                {news.relatedSymbols.slice(0, 3).map((symbol, index) => (
                  <View key={index} style={styles.symbolTag}>
                    <Text style={styles.symbolText}>{symbol}</Text>
                  </View>
                ))}
                {news.relatedSymbols.length > 3 && (
                  <Text style={styles.moreSymbols}>+{news.relatedSymbols.length - 3}</Text>
                )}
              </View>
            )}
          </View>
        </View>
      ))}
    </View>
  );

  const renderEvents = () => (
    <View style={styles.content}>
      {economicEvents.map((event) => (
        <View key={event.id} style={styles.eventCard}>
          <View style={styles.eventHeader}>
            <Text style={styles.eventName}>{event.event}</Text>
            <View style={[styles.eventImpactBadge, { backgroundColor: getImpactColor(event.impact) }]}>
              <Text style={styles.badgeText}>{event.impact.toUpperCase()}</Text>
            </View>
          </View>
          
          <View style={styles.eventTime}>
            <Icon name="clock" size={14} color="#6B7280" />
            <Text style={styles.timeText}>{event.time}</Text>
          </View>
          
          <Text style={styles.eventDescription}>{event.description}</Text>
          
          <View style={styles.eventData}>
            <View style={styles.dataRow}>
              <Text style={styles.dataLabel}>Previous:</Text>
              <Text style={styles.dataValue}>{event.previous}</Text>
            </View>
            <View style={styles.dataRow}>
              <Text style={styles.dataLabel}>Forecast:</Text>
              <Text style={styles.dataValue}>{event.forecast}</Text>
            </View>
            {event.actual && (
              <View style={styles.dataRow}>
                <Text style={styles.dataLabel}>Actual:</Text>
                <Text style={[styles.dataValue, { color: '#10B981', fontWeight: '700' }]}>
                  {event.actual}
                </Text>
              </View>
            )}
          </View>
        </View>
      ))}
    </View>
  );

  const renderSentiment = () => (
    <View style={styles.content}>
      {sentimentIndicators.map((indicator, index) => (
        <View key={index} style={styles.sentimentCard}>
          <View style={styles.sentimentHeader}>
            <Text style={styles.sentimentName}>{indicator.name}</Text>
            <View style={[styles.levelBadge, { backgroundColor: getLevelColor(indicator.level) }]}>
              <Text style={styles.badgeText}>{indicator.level.toUpperCase()}</Text>
            </View>
          </View>
          
          <View style={styles.sentimentValue}>
            <Text style={styles.valueText}>{indicator.value}</Text>
            <Text style={[styles.changeText, { color: indicator.change > 0 ? '#10B981' : '#EF4444' }]}>
              {indicator.change > 0 ? '+' : ''}{indicator.change}
            </Text>
          </View>
          
          <Text style={styles.sentimentDescription}>{indicator.description}</Text>
        </View>
      ))}
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Tab Selector */}
      <View style={styles.tabSelector}>
        {tabs.map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[
              styles.tabButton,
              selectedTab === tab.key && styles.tabButtonActive
            ]}
            onPress={() => setSelectedTab(tab.key)}
          >
            <Icon 
              name={tab.icon as any} 
              size={16} 
              color={selectedTab === tab.key ? '#FFFFFF' : '#6B7280'} 
            />
            <Text style={[
              styles.tabText,
              selectedTab === tab.key && styles.tabTextActive
            ]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {selectedTab === 'news' && renderNews()}
        {selectedTab === 'events' && renderEvents()}
        {selectedTab === 'sentiment' && renderSentiment()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  tabSelector: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 12,
    padding: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
  },
  tabButtonActive: {
    backgroundColor: '#3B82F6',
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    marginLeft: 4,
  },
  tabTextActive: {
    color: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  newsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  newsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  newsMeta: {
    flex: 1,
  },
  newsSource: {
    fontSize: 12,
    fontWeight: '600',
    color: '#3B82F6',
  },
  newsTime: {
    fontSize: 11,
    color: '#6B7280',
    marginTop: 2,
  },
  newsBadges: {
    flexDirection: 'row',
    gap: 6,
  },
  impactBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  sentimentBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#FFFFFF',
    marginLeft: 2,
  },
  newsTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    lineHeight: 22,
    marginBottom: 8,
  },
  newsSummary: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 12,
  },
  newsFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  newsCategory: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 4,
  },
  relatedSymbols: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  symbolTag: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  symbolText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#6B7280',
  },
  moreSymbols: {
    fontSize: 10,
    color: '#6B7280',
  },
  eventCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  eventHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  eventName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
    marginRight: 12,
  },
  eventImpactBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  eventTime: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  timeText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 4,
  },
  eventDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 12,
  },
  eventData: {
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
  },
  dataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  dataLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  dataValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#111827',
  },
  sentimentCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  sentimentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  sentimentName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
    marginRight: 12,
  },
  levelBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  sentimentValue: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  valueText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginRight: 12,
  },
  changeText: {
    fontSize: 14,
    fontWeight: '600',
  },
  sentimentDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
});

export default SwingTradingMarketSentiment;
