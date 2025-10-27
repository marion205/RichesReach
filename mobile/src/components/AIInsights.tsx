/**
 * AI-Powered Market Insights
 * Advanced AI analysis and predictions
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { useQuery, useMutation, gql } from '@apollo/client';
import { Ionicons } from '@expo/vector-icons';

// GraphQL Queries and Mutations
const GET_MARKET_INSIGHTS = gql`
  query GetMarketInsights($limit: Int, $category: String) {
    marketInsights(limit: $limit, category: $category) {
      id
      title
      summary
      category
      confidence
      impact
      sentiment
      timestamp
      symbols
      data {
        priceTarget
        probability
        timeframe
        reasoning
      }
      source
      tags
    }
  }
`;

const GET_AI_PREDICTIONS = gql`
  query GetAIPredictions($symbol: String!) {
    aiPredictions(symbol: $symbol) {
      symbol
      predictions {
        timeframe
        priceTarget
        probability
        direction
        confidence
        factors
      }
      technicalAnalysis {
        trend
        support
        resistance
        indicators
      }
      sentimentAnalysis {
        overall
        news
        social
        analyst
      }
    }
  }
`;

const GET_MARKET_REGIME = gql`
  query GetMarketRegime {
    marketRegime {
      current
      confidence
      transitions
      indicators {
        volatility
        trend
        momentum
        volume
      }
      recommendations
    }
  }
`;

const GET_ORACLE_INSIGHTS = gql`
  query GetOracleInsights($query: String!) {
    oracleInsights(query: $query) {
      id
      question
      answer
      confidence
      sources
      timestamp
      relatedInsights
    }
  }
`;

const SAVE_INSIGHT = gql`
  mutation SaveInsight($insightId: ID!) {
    saveInsight(insightId: $insightId) {
      success
      message
    }
  }
`;

const SHARE_INSIGHT = gql`
  mutation ShareInsight($insightId: ID!, $platform: String!) {
    shareInsight(insightId: $insightId, platform: $platform) {
      success
      message
    }
  }
`;

interface MarketInsight {
  id: string;
  title: string;
  summary: string;
  category: 'bullish' | 'bearish' | 'neutral' | 'volatile';
  confidence: number;
  impact: 'low' | 'medium' | 'high' | 'critical';
  sentiment: number;
  timestamp: string;
  symbols: string[];
  data: {
    priceTarget: number;
    probability: number;
    timeframe: string;
    reasoning: string;
  };
  source: string;
  tags: string[];
}

interface AIPrediction {
  symbol: string;
  predictions: {
    timeframe: string;
    priceTarget: number;
    probability: number;
    direction: 'up' | 'down' | 'sideways';
    confidence: number;
    factors: string[];
  }[];
  technicalAnalysis: {
    trend: string;
    support: number;
    resistance: number;
    indicators: any;
  };
  sentimentAnalysis: {
    overall: number;
    news: number;
    social: number;
    analyst: number;
  };
}

interface MarketRegime {
  current: string;
  confidence: number;
  transitions: any[];
  indicators: {
    volatility: number;
    trend: number;
    momentum: number;
    volume: number;
  };
  recommendations: string[];
}

interface OracleInsight {
  id: string;
  question: string;
  answer: string;
  confidence: number;
  sources: string[];
  timestamp: string;
  relatedInsights: string[];
}

interface AIInsightsProps {
  userId: string;
  onInsightSelect?: (insight: MarketInsight) => void;
  onPredictionSelect?: (prediction: AIPrediction) => void;
}

export const AIInsights: React.FC<AIInsightsProps> = ({
  userId,
  onInsightSelect,
  onPredictionSelect,
}) => {
  const [activeTab, setActiveTab] = useState<'insights' | 'predictions' | 'regime' | 'oracle'>('insights');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('AAPL');
  const [refreshing, setRefreshing] = useState(false);
  const [oracleQuery, setOracleQuery] = useState('');

  const { data: insightsData, loading: insightsLoading, refetch: refetchInsights } = useQuery(
    GET_MARKET_INSIGHTS,
    {
      variables: { limit: 20, category: selectedCategory === 'all' ? null : selectedCategory },
    }
  );

  const { data: predictionsData, loading: predictionsLoading, refetch: refetchPredictions } = useQuery(
    GET_AI_PREDICTIONS,
    {
      variables: { symbol: selectedSymbol },
    }
  );

  const { data: regimeData, loading: regimeLoading, refetch: refetchRegime } = useQuery(
    GET_MARKET_REGIME
  );

  const { data: oracleData, loading: oracleLoading, refetch: refetchOracle } = useQuery(
    GET_ORACLE_INSIGHTS,
    {
      variables: { query: oracleQuery },
      skip: !oracleQuery,
    }
  );

  const [saveInsight] = useMutation(SAVE_INSIGHT);
  const [shareInsight] = useMutation(SHARE_INSIGHT);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refetchInsights(),
        refetchPredictions(),
        refetchRegime(),
        refetchOracle(),
      ]);
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleSaveInsight = async (insightId: string) => {
    try {
      const result = await saveInsight({ variables: { insightId } });
      if (result.data?.saveInsight?.success) {
        Alert.alert('Success', 'Insight saved to your collection!');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to save insight');
    }
  };

  const handleShareInsight = async (insightId: string, platform: string) => {
    try {
      const result = await shareInsight({ variables: { insightId, platform } });
      if (result.data?.shareInsight?.success) {
        Alert.alert('Success', `Insight shared to ${platform}!`);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to share insight');
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'bullish': return '#00ff88';
      case 'bearish': return '#ff4444';
      case 'volatile': return '#ffbb00';
      case 'neutral': return '#888';
      default: return '#007bff';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'critical': return '#ff4444';
      case 'high': return '#ff8800';
      case 'medium': return '#ffbb00';
      case 'low': return '#00ff88';
      default: return '#888';
    }
  };

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.3) return '#00ff88';
    if (sentiment < -0.3) return '#ff4444';
    return '#ffbb00';
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const renderInsightCard = (insight: MarketInsight) => (
    <TouchableOpacity
      key={insight.id}
      style={styles.insightCard}
      onPress={() => onInsightSelect?.(insight)}
    >
      <View style={styles.insightHeader}>
        <View style={styles.insightTitleRow}>
          <Text style={styles.insightTitle}>{insight.title}</Text>
          <View style={[
            styles.categoryBadge,
            { backgroundColor: getCategoryColor(insight.category) }
          ]}>
            <Text style={styles.categoryText}>{insight.category.toUpperCase()}</Text>
          </View>
        </View>
        <Text style={styles.insightTimestamp}>{formatTimestamp(insight.timestamp)}</Text>
      </View>

      <Text style={styles.insightSummary}>{insight.summary}</Text>

      <View style={styles.insightMetrics}>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>Confidence</Text>
          <Text style={styles.metricValue}>{insight.confidence.toFixed(1)}%</Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>Impact</Text>
          <Text style={[
            styles.metricValue,
            { color: getImpactColor(insight.impact) }
          ]}>
            {insight.impact.toUpperCase()}
          </Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>Sentiment</Text>
          <Text style={[
            styles.metricValue,
            { color: getSentimentColor(insight.sentiment) }
          ]}>
            {insight.sentiment > 0 ? '+' : ''}{insight.sentiment.toFixed(2)}
          </Text>
        </View>
      </View>

      {insight.data && (
        <View style={styles.insightData}>
          <Text style={styles.dataTitle}>AI Analysis</Text>
          <Text style={styles.dataText}>
            Price Target: ${insight.data.priceTarget.toFixed(2)} 
            ({insight.data.probability.toFixed(1)}% probability)
          </Text>
          <Text style={styles.dataText}>
            Timeframe: {insight.data.timeframe}
          </Text>
          <Text style={styles.dataText}>
            Reasoning: {insight.data.reasoning}
          </Text>
        </View>
      )}

      <View style={styles.insightSymbols}>
        {insight.symbols.map((symbol, index) => (
          <View key={index} style={styles.symbolTag}>
            <Text style={styles.symbolText}>{symbol}</Text>
          </View>
        ))}
      </View>

      <View style={styles.insightActions}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleSaveInsight(insight.id)}
        >
          <Ionicons name="bookmark-outline" size={20} color="#888" />
          <Text style={styles.actionText}>Save</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleShareInsight(insight.id, 'twitter')}
        >
          <Ionicons name="share-outline" size={20} color="#888" />
          <Text style={styles.actionText}>Share</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Ionicons name="chatbubble-outline" size={20} color="#888" />
          <Text style={styles.actionText}>Discuss</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  const renderPredictionsTab = () => {
    if (!predictionsData?.aiPredictions) return null;

    const prediction = predictionsData.aiPredictions;

    return (
      <ScrollView style={styles.tabContent}>
        {/* Symbol Selector */}
        <View style={styles.symbolSelector}>
          {['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'].map((symbol) => (
            <TouchableOpacity
              key={symbol}
              style={[
                styles.symbolButton,
                selectedSymbol === symbol && styles.activeSymbolButton,
              ]}
              onPress={() => setSelectedSymbol(symbol)}
            >
              <Text style={[
                styles.symbolButtonText,
                selectedSymbol === symbol && styles.activeSymbolButtonText,
              ]}>
                {symbol}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Predictions */}
        <View style={styles.predictionsCard}>
          <Text style={styles.predictionsTitle}>AI Predictions for {prediction.symbol}</Text>
          {prediction.predictions.map((pred, index) => (
            <View key={index} style={styles.predictionItem}>
              <View style={styles.predictionHeader}>
                <Text style={styles.predictionTimeframe}>{pred.timeframe}</Text>
                <View style={[
                  styles.predictionDirection,
                  { backgroundColor: pred.direction === 'up' ? '#00ff88' : pred.direction === 'down' ? '#ff4444' : '#888' }
                ]}>
                  <Text style={styles.predictionDirectionText}>
                    {pred.direction.toUpperCase()}
                  </Text>
                </View>
              </View>
              <Text style={styles.predictionTarget}>
                Target: ${pred.priceTarget.toFixed(2)} ({pred.probability.toFixed(1)}% probability)
              </Text>
              <Text style={styles.predictionConfidence}>
                Confidence: {pred.confidence.toFixed(1)}%
              </Text>
              <View style={styles.predictionFactors}>
                <Text style={styles.factorsTitle}>Key Factors:</Text>
                {pred.factors.map((factor, factorIndex) => (
                  <Text key={factorIndex} style={styles.factorText}>• {factor}</Text>
                ))}
              </View>
            </View>
          ))}
        </View>

        {/* Technical Analysis */}
        <View style={styles.technicalCard}>
          <Text style={styles.technicalTitle}>Technical Analysis</Text>
          <View style={styles.technicalMetrics}>
            <View style={styles.technicalMetric}>
              <Text style={styles.technicalLabel}>Trend</Text>
              <Text style={styles.technicalValue}>{prediction.technicalAnalysis.trend}</Text>
            </View>
            <View style={styles.technicalMetric}>
              <Text style={styles.technicalLabel}>Support</Text>
              <Text style={styles.technicalValue}>${prediction.technicalAnalysis.support.toFixed(2)}</Text>
            </View>
            <View style={styles.technicalMetric}>
              <Text style={styles.technicalLabel}>Resistance</Text>
              <Text style={styles.technicalValue}>${prediction.technicalAnalysis.resistance.toFixed(2)}</Text>
            </View>
          </View>
        </View>

        {/* Sentiment Analysis */}
        <View style={styles.sentimentCard}>
          <Text style={styles.sentimentTitle}>Sentiment Analysis</Text>
          <View style={styles.sentimentMetrics}>
            <View style={styles.sentimentMetric}>
              <Text style={styles.sentimentLabel}>Overall</Text>
              <Text style={[
                styles.sentimentValue,
                { color: getSentimentColor(prediction.sentimentAnalysis.overall) }
              ]}>
                {prediction.sentimentAnalysis.overall.toFixed(2)}
              </Text>
            </View>
            <View style={styles.sentimentMetric}>
              <Text style={styles.sentimentLabel}>News</Text>
              <Text style={[
                styles.sentimentValue,
                { color: getSentimentColor(prediction.sentimentAnalysis.news) }
              ]}>
                {prediction.sentimentAnalysis.news.toFixed(2)}
              </Text>
            </View>
            <View style={styles.sentimentMetric}>
              <Text style={styles.sentimentLabel}>Social</Text>
              <Text style={[
                styles.sentimentValue,
                { color: getSentimentColor(prediction.sentimentAnalysis.social) }
              ]}>
                {prediction.sentimentAnalysis.social.toFixed(2)}
              </Text>
            </View>
            <View style={styles.sentimentMetric}>
              <Text style={styles.sentimentLabel}>Analyst</Text>
              <Text style={[
                styles.sentimentValue,
                { color: getSentimentColor(prediction.sentimentAnalysis.analyst) }
              ]}>
                {prediction.sentimentAnalysis.analyst.toFixed(2)}
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    );
  };

  const renderRegimeTab = () => {
    if (!regimeData?.marketRegime) return null;

    const regime = regimeData.marketRegime;

    return (
      <ScrollView style={styles.tabContent}>
        <View style={styles.regimeCard}>
          <Text style={styles.regimeTitle}>Current Market Regime</Text>
          <View style={styles.regimeHeader}>
            <Text style={styles.regimeCurrent}>{regime.current.toUpperCase()}</Text>
            <Text style={styles.regimeConfidence}>
              Confidence: {regime.confidence.toFixed(1)}%
            </Text>
          </View>
        </View>

        <View style={styles.indicatorsCard}>
          <Text style={styles.indicatorsTitle}>Market Indicators</Text>
          <View style={styles.indicatorsGrid}>
            <View style={styles.indicatorItem}>
              <Text style={styles.indicatorLabel}>Volatility</Text>
              <Text style={styles.indicatorValue}>{regime.indicators.volatility.toFixed(2)}</Text>
            </View>
            <View style={styles.indicatorItem}>
              <Text style={styles.indicatorLabel}>Trend</Text>
              <Text style={styles.indicatorValue}>{regime.indicators.trend.toFixed(2)}</Text>
            </View>
            <View style={styles.indicatorItem}>
              <Text style={styles.indicatorLabel}>Momentum</Text>
              <Text style={styles.indicatorValue}>{regime.indicators.momentum.toFixed(2)}</Text>
            </View>
            <View style={styles.indicatorItem}>
              <Text style={styles.indicatorLabel}>Volume</Text>
              <Text style={styles.indicatorValue}>{regime.indicators.volume.toFixed(2)}</Text>
            </View>
          </View>
        </View>

        <View style={styles.recommendationsCard}>
          <Text style={styles.recommendationsTitle}>AI Recommendations</Text>
          {regime.recommendations.map((recommendation, index) => (
            <View key={index} style={styles.recommendationItem}>
              <Ionicons name="bulb-outline" size={20} color="#ffbb00" />
              <Text style={styles.recommendationText}>{recommendation}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    );
  };

  const renderOracleTab = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.oracleCard}>
        <Text style={styles.oracleTitle}>Oracle AI Assistant</Text>
        <Text style={styles.oracleSubtitle}>
          Ask any market question and get AI-powered insights
        </Text>
        
        <View style={styles.oracleInput}>
          <Text style={styles.oracleInputLabel}>Your Question:</Text>
          <TouchableOpacity
            style={styles.oracleInputField}
            onPress={() => {
              // In a real app, this would open a text input
              setOracleQuery('What is the outlook for tech stocks?');
            }}
          >
            <Text style={styles.oracleInputText}>
              {oracleQuery || 'Tap to ask a question...'}
            </Text>
          </TouchableOpacity>
        </View>

        {oracleData?.oracleInsights && (
          <View style={styles.oracleResponse}>
            <Text style={styles.oracleResponseTitle}>AI Response:</Text>
            <Text style={styles.oracleResponseText}>
              {oracleData.oracleInsights.answer}
            </Text>
            <Text style={styles.oracleResponseConfidence}>
              Confidence: {oracleData.oracleInsights.confidence.toFixed(1)}%
            </Text>
            <View style={styles.oracleResponseSources}>
              <Text style={styles.sourcesTitle}>Sources:</Text>
              {oracleData.oracleInsights.sources.map((source, index) => (
                <Text key={index} style={styles.sourceText}>• {source}</Text>
              ))}
            </View>
          </View>
        )}
      </View>
    </ScrollView>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'insights':
        return (
          <ScrollView
            style={styles.tabContent}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
          >
            {/* Category Filter */}
            <View style={styles.categoryFilter}>
              {['all', 'bullish', 'bearish', 'volatile', 'neutral'].map((category) => (
                <TouchableOpacity
                  key={category}
                  style={[
                    styles.categoryButton,
                    selectedCategory === category && styles.activeCategoryButton,
                  ]}
                  onPress={() => setSelectedCategory(category)}
                >
                  <Text style={[
                    styles.categoryButtonText,
                    selectedCategory === category && styles.activeCategoryButtonText,
                  ]}>
                    {category.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Insights List */}
            {insightsData?.marketInsights?.map(renderInsightCard)}
          </ScrollView>
        );
      case 'predictions':
        return renderPredictionsTab();
      case 'regime':
        return renderRegimeTab();
      case 'oracle':
        return renderOracleTab();
      default:
        return null;
    }
  };

  if (insightsLoading || predictionsLoading || regimeLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0F0" />
        <Text style={styles.loadingText}>Loading AI insights...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AI Market Insights</Text>
        <TouchableOpacity style={styles.headerButton}>
          <Ionicons name="refresh-outline" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        {[
          { key: 'insights', label: 'Insights', icon: 'bulb-outline' },
          { key: 'predictions', label: 'Predictions', icon: 'trending-up-outline' },
          { key: 'regime', label: 'Regime', icon: 'analytics-outline' },
          { key: 'oracle', label: 'Oracle', icon: 'chatbubble-outline' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[
              styles.tabButton,
              activeTab === tab.key && styles.activeTabButton,
            ]}
            onPress={() => setActiveTab(tab.key as any)}
          >
            <Ionicons
              name={tab.icon as any}
              size={20}
              color={activeTab === tab.key ? '#0F0' : '#888'}
            />
            <Text style={[
              styles.tabText,
              activeTab === tab.key && styles.activeTabText,
            ]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Tab Content */}
      <View style={styles.content}>
        {renderTabContent()}
      </View>
    </View>
  );
};

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  loadingText: {
    color: '#0F0',
    marginTop: 10,
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1a1a1a',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerButton: {
    padding: 5,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    paddingHorizontal: 20,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    marginHorizontal: 5,
  },
  activeTabButton: {
    borderBottomWidth: 2,
    borderBottomColor: '#0F0',
  },
  tabText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#888',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#0F0',
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
  },
  categoryFilter: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1a1a1a',
  },
  categoryButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
    borderRadius: 20,
    backgroundColor: '#333',
  },
  activeCategoryButton: {
    backgroundColor: '#007bff',
  },
  categoryButtonText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '500',
  },
  activeCategoryButtonText: {
    fontWeight: 'bold',
  },
  insightCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  insightHeader: {
    marginBottom: 15,
  },
  insightTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 5,
  },
  insightTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    flex: 1,
  },
  categoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  categoryText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#000',
  },
  insightTimestamp: {
    fontSize: 12,
    color: '#888',
  },
  insightSummary: {
    fontSize: 16,
    color: '#ccc',
    lineHeight: 22,
    marginBottom: 15,
  },
  insightMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 15,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#333',
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  metricItem: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  insightData: {
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 12,
    marginBottom: 15,
  },
  dataTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  dataText: {
    fontSize: 14,
    color: '#ccc',
    marginBottom: 4,
  },
  insightSymbols: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 15,
  },
  symbolTag: {
    backgroundColor: '#007bff',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginRight: 8,
    marginBottom: 8,
  },
  symbolText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: 'bold',
  },
  insightActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  actionText: {
    marginLeft: 5,
    fontSize: 14,
    color: '#888',
  },
  symbolSelector: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1a1a1a',
  },
  symbolButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
    borderRadius: 20,
    backgroundColor: '#333',
  },
  activeSymbolButton: {
    backgroundColor: '#007bff',
  },
  symbolButtonText: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '500',
  },
  activeSymbolButtonText: {
    fontWeight: 'bold',
  },
  predictionsCard: {
    backgroundColor: '#1a1a1a',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  predictionsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  predictionItem: {
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
  },
  predictionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  predictionTimeframe: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  predictionDirection: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  predictionDirectionText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#000',
  },
  predictionTarget: {
    fontSize: 14,
    color: '#ccc',
    marginBottom: 5,
  },
  predictionConfidence: {
    fontSize: 14,
    color: '#888',
    marginBottom: 10,
  },
  predictionFactors: {
    marginTop: 10,
  },
  factorsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  factorText: {
    fontSize: 14,
    color: '#ccc',
    marginBottom: 2,
  },
  technicalCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  technicalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  technicalMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  technicalMetric: {
    alignItems: 'center',
  },
  technicalLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 4,
  },
  technicalValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  sentimentCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  sentimentTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  sentimentMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  sentimentMetric: {
    alignItems: 'center',
  },
  sentimentLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 4,
  },
  sentimentValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  regimeCard: {
    backgroundColor: '#1a1a1a',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  regimeTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  regimeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  regimeCurrent: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0F0',
  },
  regimeConfidence: {
    fontSize: 14,
    color: '#888',
  },
  indicatorsCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  indicatorsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  indicatorsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  indicatorItem: {
    width: '48%',
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
    alignItems: 'center',
  },
  indicatorLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 5,
  },
  indicatorValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  recommendationsCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  recommendationsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  recommendationText: {
    flex: 1,
    marginLeft: 10,
    fontSize: 14,
    color: '#fff',
  },
  oracleCard: {
    backgroundColor: '#1a1a1a',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  oracleTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  oracleSubtitle: {
    fontSize: 14,
    color: '#888',
    marginBottom: 20,
  },
  oracleInput: {
    marginBottom: 20,
  },
  oracleInputLabel: {
    fontSize: 14,
    color: '#ccc',
    marginBottom: 8,
  },
  oracleInputField: {
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
    borderWidth: 1,
    borderColor: '#555',
  },
  oracleInputText: {
    fontSize: 16,
    color: '#fff',
  },
  oracleResponse: {
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
  },
  oracleResponseTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  oracleResponseText: {
    fontSize: 14,
    color: '#ccc',
    lineHeight: 20,
    marginBottom: 10,
  },
  oracleResponseConfidence: {
    fontSize: 12,
    color: '#888',
    marginBottom: 10,
  },
  oracleResponseSources: {
    marginTop: 10,
  },
  sourcesTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  sourceText: {
    fontSize: 12,
    color: '#888',
    marginBottom: 2,
  },
});

export default AIInsights;
