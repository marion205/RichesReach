import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const GET_RUST_SENTIMENT_ANALYSIS = gql`
  query GetRustSentimentAnalysis($symbol: String!) {
    rustSentimentAnalysis(symbol: $symbol) {
      symbol
      overallSentiment
      sentimentScore
      newsSentiment {
        score
        articleCount
        positiveArticles
        negativeArticles
        neutralArticles
        topHeadlines
      }
      socialSentiment {
        score
        mentions24h
        positiveMentions
        negativeMentions
        engagementScore
        trending
      }
      confidence
      timestamp
    }
  }
`;

interface RustSentimentWidgetProps {
  symbol: string;
}

export default function RustSentimentWidget({ symbol }: RustSentimentWidgetProps) {
  const { data, loading, error } = useQuery(GET_RUST_SENTIMENT_ANALYSIS, {
    variables: { symbol },
    skip: !symbol,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="small" color="#007AFF" />
        <Text style={styles.loadingText}>Loading sentiment...</Text>
      </View>
    );
  }

  if (error || !data?.rustSentimentAnalysis) {
    return null;
  }

  const analysis = data.rustSentimentAnalysis;
  const news = analysis.newsSentiment || {};
  const social = analysis.socialSentiment || {};

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'BULLISH': return '#10B981';
      case 'BEARISH': return '#EF4444';
      default: return '#6B7280';
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="trending-up" size={16} color={getSentimentColor(analysis.overallSentiment)} />
        <Text style={styles.title}>Sentiment Analysis</Text>
        <View style={[styles.sentimentBadge, { backgroundColor: getSentimentColor(analysis.overallSentiment) + '20' }]}>
          <Text style={[styles.sentimentText, { color: getSentimentColor(analysis.overallSentiment) }]}>
            {analysis.overallSentiment}
          </Text>
        </View>
      </View>

      {/* Overall Score */}
      <View style={styles.scoreContainer}>
        <Text style={styles.scoreLabel}>Overall Score</Text>
        <Text style={[styles.scoreValue, { color: getSentimentColor(analysis.overallSentiment) }]}>
          {(analysis.sentimentScore * 100).toFixed(0)}%
        </Text>
      </View>

      {/* News Sentiment */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>News Sentiment</Text>
        <View style={styles.row}>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Articles</Text>
            <Text style={styles.metricValue}>{news.articleCount || 0}</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Positive</Text>
            <Text style={[styles.metricValue, { color: '#10B981' }]}>{news.positiveArticles || 0}</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Negative</Text>
            <Text style={[styles.metricValue, { color: '#EF4444' }]}>{news.negativeArticles || 0}</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Score</Text>
            <Text style={styles.metricValue}>{(news.score * 100).toFixed(0)}%</Text>
          </View>
        </View>
      </View>

      {/* Social Sentiment */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Social Sentiment</Text>
        <View style={styles.row}>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Mentions (24h)</Text>
            <Text style={styles.metricValue}>{social.mentions24h || 0}</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Engagement</Text>
            <Text style={styles.metricValue}>{(social.engagementScore * 100).toFixed(0)}%</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Score</Text>
            <Text style={styles.metricValue}>{(social.score * 100).toFixed(0)}%</Text>
          </View>
          {social.trending && (
            <View style={styles.metric}>
              <Icon name="trending-up" size={16} color="#EF4444" />
              <Text style={styles.trendingText}>Trending</Text>
            </View>
          )}
        </View>
      </View>

      {/* Confidence */}
      <View style={styles.confidenceContainer}>
        <Text style={styles.confidenceLabel}>Confidence</Text>
        <View style={styles.confidenceBar}>
          <View 
            style={[
              styles.confidenceFill, 
              { width: `${(analysis.confidence * 100)}%` }
            ]} 
          />
        </View>
        <Text style={styles.confidenceValue}>{(analysis.confidence * 100).toFixed(0)}%</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 8,
    flex: 1,
  },
  sentimentBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  sentimentText: {
    fontSize: 12,
    fontWeight: '600',
  },
  scoreContainer: {
    alignItems: 'center',
    marginBottom: 16,
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
  },
  scoreLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  scoreValue: {
    fontSize: 32,
    fontWeight: '700',
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
  },
  metric: {
    alignItems: 'center',
    minWidth: '22%',
    marginBottom: 8,
  },
  metricLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  trendingText: {
    fontSize: 10,
    color: '#EF4444',
    marginTop: 2,
  },
  confidenceContainer: {
    marginTop: 8,
  },
  confidenceLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  confidenceBar: {
    height: 8,
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 4,
  },
  confidenceFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 4,
  },
  confidenceValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'right',
  },
  loadingText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 8,
  },
});

