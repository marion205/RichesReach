import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import AdvancedChart from '../components/AdvancedChart';
import { UI } from '../constants';

const RESEARCH_QUERY = gql`
  query Research($s: String!) {
    researchHub(symbol: $s) {
      symbol
      company {
        name
        sector
        marketCap
        country
        website
      }
      quote {
        currentPrice
        change
        changePercent
        high
        low
        volume
      }
      technicals {
        rsi
        macd
        macdhistogram
        movingAverage50
        movingAverage200
        supportLevel
        resistanceLevel
        impliedVolatility
      }
      sentiment {
        sentiment_label
        sentiment_score
        article_count
        confidence
      }
      macro {
        vix
        market_sentiment
        risk_appetite
      }
      marketRegime {
        market_regime
        confidence
        recommended_strategy
      }
      peers
      updatedAt
    }
  }
`;

const CHART_QUERY = gql`
  query Chart($s: String!, $interval: String = "1D", $limit: Int = 180, $inds: [String!] = ["SMA20", "SMA50", "EMA12", "EMA26", "RSI", "MACD", "BB"]) {
    stockChartData(symbol: $s, timeframe: $interval, interval: $interval, limit: $limit, indicators: $inds) {
      symbol
      interval
      limit
      currentPrice
      change
      changePercent
      data {
        timestamp
        open
        high
        low
        close
        volume
      }
      indicators {
        SMA20
        SMA50
        EMA12
        EMA26
        BB_upper
        BB_middle
        BB_lower
        RSI14
        MACD
        MACD_signal
        MACD_hist
      }
    }
  }
`;

const ResearchScreen: React.FC = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [chartInterval, setChartInterval] = useState('1D');

  const { data: researchData, loading: researchLoading, error: researchError, refetch: refetchResearch } = useQuery(RESEARCH_QUERY, {
    variables: { s: symbol },
    skip: !symbol,
  });

  const { data: chartData, loading: chartLoading, error: chartError } = useQuery(CHART_QUERY, {
    variables: { 
      s: symbol, 
      interval: chartInterval, 
      limit: 180,
      inds: ["SMA20", "SMA50", "EMA12", "EMA26", "RSI", "MACD", "BB"]
    },
    skip: !symbol,
  });

  const research = researchData?.researchHub;
  const chart = chartData?.stockChartData;

  const formatMarketCap = (cap: number) => {
    if (cap >= 1e12) return `$${(cap / 1e12).toFixed(1)}T`;
    if (cap >= 1e9) return `$${(cap / 1e9).toFixed(1)}B`;
    if (cap >= 1e6) return `$${(cap / 1e6).toFixed(1)}M`;
    return `$${cap.toLocaleString()}`;
  };

  const getSentimentColor = (label: string) => {
    switch (label) {
      case 'BULLISH': return '#22C55E';
      case 'BEARISH': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getRegimeColor = (regime: string) => {
    switch (regime) {
      case 'BULL': return '#22C55E';
      case 'BEAR': return '#EF4444';
      default: return '#F59E0B';
    }
  };

  if (researchLoading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Research Hub</Text>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={UI.accent} />
          <Text style={styles.loadingText}>Loading research data...</Text>
        </View>
      </View>
    );
  }

  if (researchError) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Research Hub</Text>
        </View>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color={UI.error} />
          <Text style={styles.errorText}>Failed to load research data</Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => refetchResearch()}>
            <Icon name="refresh-cw" size={16} color={UI.accent} />
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Research Hub</Text>
        <View style={styles.searchContainer}>
          <TextInput
            style={styles.searchInput}
            value={symbol}
            onChangeText={setSymbol}
            placeholder="Enter symbol (e.g., AAPL)"
            placeholderTextColor={UI.sub}
            autoCapitalize="characters"
          />
          <TouchableOpacity style={styles.searchButton} onPress={() => refetchResearch()}>
            <Icon name="search" size={20} color={UI.accent} />
          </TouchableOpacity>
        </View>
      </View>

      {research && (
        <>
          {/* Company Header */}
          <View style={styles.card}>
            <View style={styles.companyHeader}>
              <View>
                <Text style={styles.companyName}>{research.company.name}</Text>
                <Text style={styles.sector}>{research.company.sector}</Text>
                <Text style={styles.marketCap}>{formatMarketCap(research.company.marketCap)}</Text>
              </View>
              <View style={styles.priceContainer}>
                <Text style={styles.currentPrice}>${research.quote.currentPrice.toFixed(2)}</Text>
                <Text style={[
                  styles.change,
                  { color: research.quote.change >= 0 ? '#22C55E' : '#EF4444' }
                ]}>
                  {research.quote.change >= 0 ? '+' : ''}{research.quote.change.toFixed(2)} ({research.quote.changePercent.toFixed(2)}%)
                </Text>
              </View>
            </View>
          </View>

          {/* Advanced Chart */}
          {chart && (
            <View style={styles.card}>
              <View style={styles.chartHeader}>
                <Text style={styles.chartTitle}>Price Chart</Text>
                <View style={styles.intervalSelector}>
                  {['1D', '1W', '1M', '3M', '1Y'].map(interval => (
                    <TouchableOpacity
                      key={interval}
                      style={[
                        styles.intervalButton,
                        chartInterval === interval && styles.intervalButtonActive
                      ]}
                      onPress={() => setChartInterval(interval)}
                    >
                      <Text style={[
                        styles.intervalText,
                        chartInterval === interval && styles.intervalTextActive
                      ]}>
                        {interval}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
              {chartLoading ? (
                <View style={styles.chartLoading}>
                  <ActivityIndicator size="small" color={UI.accent} />
                </View>
              ) : (
                <AdvancedChart
                  data={chart.data}
                  indicators={chart.indicators}
                  width={350}
                  height={200}
                />
              )}
            </View>
          )}

          {/* Key Metrics Cards */}
          <View style={styles.metricsGrid}>
            {/* Valuation */}
            <View style={styles.metricCard}>
              <Text style={styles.metricTitle}>Valuation</Text>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>P/E Ratio</Text>
                <Text style={styles.metricValue}>N/A</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>P/B Ratio</Text>
                <Text style={styles.metricValue}>N/A</Text>
              </View>
            </View>

            {/* Technicals */}
            <View style={styles.metricCard}>
              <Text style={styles.metricTitle}>Technicals</Text>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>RSI (14)</Text>
                <Text style={styles.metricValue}>{research.technicals.rsi.toFixed(1)}</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>MACD</Text>
                <Text style={styles.metricValue}>{research.technicals.macd.toFixed(3)}</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>MA 50</Text>
                <Text style={styles.metricValue}>${research.technicals.movingAverage50.toFixed(2)}</Text>
              </View>
            </View>

            {/* Sentiment */}
            <View style={styles.metricCard}>
              <Text style={styles.metricTitle}>Sentiment</Text>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>News Sentiment</Text>
                <Text style={[
                  styles.metricValue,
                  { color: getSentimentColor(research.sentiment.sentiment_label) }
                ]}>
                  {research.sentiment.sentiment_label}
                </Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Score</Text>
                <Text style={styles.metricValue}>{research.sentiment.sentiment_score.toFixed(2)}</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Articles</Text>
                <Text style={styles.metricValue}>{research.sentiment.article_count}</Text>
              </View>
            </View>

            {/* Macro */}
            <View style={styles.metricCard}>
              <Text style={styles.metricTitle}>Macro</Text>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>VIX</Text>
                <Text style={styles.metricValue}>{research.macro.vix.toFixed(1)}</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Market Sentiment</Text>
                <Text style={styles.metricValue}>{research.macro.market_sentiment}</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Risk Appetite</Text>
                <Text style={styles.metricValue}>{(research.macro.risk_appetite * 100).toFixed(0)}%</Text>
              </View>
            </View>

            {/* Market Regime */}
            <View style={styles.metricCard}>
              <Text style={styles.metricTitle}>Market Regime</Text>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Current Regime</Text>
                <Text style={[
                  styles.metricValue,
                  { color: getRegimeColor(research.marketRegime.market_regime) }
                ]}>
                  {research.marketRegime.market_regime}
                </Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Confidence</Text>
                <Text style={styles.metricValue}>{(research.marketRegime.confidence * 100).toFixed(0)}%</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Strategy</Text>
                <Text style={styles.metricValue}>{research.marketRegime.recommended_strategy}</Text>
              </View>
            </View>

            {/* Options Snapshot */}
            <View style={styles.metricCard}>
              <Text style={styles.metricTitle}>Options</Text>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Implied Vol</Text>
                <Text style={styles.metricValue}>{(research.technicals.impliedVolatility * 100).toFixed(1)}%</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Support</Text>
                <Text style={styles.metricValue}>${research.technicals.supportLevel.toFixed(2)}</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Resistance</Text>
                <Text style={styles.metricValue}>${research.technicals.resistanceLevel.toFixed(2)}</Text>
              </View>
            </View>
          </View>

          {/* Peers */}
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Peer Companies</Text>
            <View style={styles.peersContainer}>
              {research.peers.map((peer: string) => (
                <TouchableOpacity
                  key={peer}
                  style={styles.peerChip}
                  onPress={() => {
                    setSymbol(peer);
                    refetchResearch();
                  }}
                >
                  <Text style={styles.peerText}>{peer}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Last Updated */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>
              Last updated: {new Date(research.updatedAt).toLocaleString()}
            </Text>
          </View>
        </>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: UI.background,
  },
  header: {
    padding: 16,
    backgroundColor: UI.background,
    borderBottomWidth: 1,
    borderBottomColor: UI.border,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: UI.text,
    marginBottom: 16,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  searchInput: {
    flex: 1,
    height: 40,
    borderWidth: 1,
    borderColor: UI.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    color: UI.text,
    backgroundColor: UI.secondary,
  },
  searchButton: {
    marginLeft: 8,
    padding: 8,
    backgroundColor: UI.accent,
    borderRadius: 8,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    marginTop: 16,
    color: UI.sub,
    fontSize: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorText: {
    marginTop: 16,
    color: UI.error,
    fontSize: 16,
    textAlign: 'center',
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: UI.secondary,
    borderRadius: 8,
  },
  retryText: {
    marginLeft: 8,
    color: UI.accent,
    fontWeight: '600',
  },
  card: {
    backgroundColor: UI.background,
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
    elevation: 2,
  },
  companyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  companyName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: UI.text,
  },
  sector: {
    fontSize: 14,
    color: UI.sub,
    marginTop: 4,
  },
  marketCap: {
    fontSize: 14,
    color: UI.sub,
    marginTop: 2,
  },
  priceContainer: {
    alignItems: 'flex-end',
  },
  currentPrice: {
    fontSize: 24,
    fontWeight: 'bold',
    color: UI.text,
  },
  change: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 4,
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: UI.text,
  },
  intervalSelector: {
    flexDirection: 'row',
  },
  intervalButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginLeft: 4,
    borderRadius: 6,
    backgroundColor: UI.secondary,
  },
  intervalButtonActive: {
    backgroundColor: UI.accent,
  },
  intervalText: {
    fontSize: 12,
    color: UI.sub,
    fontWeight: '600',
  },
  intervalTextActive: {
    color: UI.background,
  },
  chartLoading: {
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
  },
  metricCard: {
    width: '48%',
    backgroundColor: UI.background,
    margin: '1%',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
    elevation: 2,
  },
  metricTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: UI.text,
    marginBottom: 12,
  },
  metricItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  metricLabel: {
    fontSize: 14,
    color: UI.sub,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: UI.text,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: UI.text,
    marginBottom: 12,
  },
  peersContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  peerChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: UI.secondary,
    borderRadius: 16,
  },
  peerText: {
    fontSize: 14,
    color: UI.accent,
    fontWeight: '600',
  },
  footer: {
    padding: 16,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: UI.sub,
  },
});

export default ResearchScreen;
