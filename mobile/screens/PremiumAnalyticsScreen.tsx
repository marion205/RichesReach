import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { useQuery } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { gql } from '@apollo/client';

const { width } = Dimensions.get('window');

// GraphQL Queries - Using premium queries for authenticated users
const GET_PREMIUM_PORTFOLIO_METRICS = gql`
  query GetPremiumPortfolioMetrics($portfolioName: String) {
    premiumPortfolioMetrics(portfolioName: $portfolioName) {
      totalValue
      totalCost
      totalReturn
      totalReturnPercent
      volatility
      sharpeRatio
      maxDrawdown
      beta
      alpha
      holdings {
        symbol
        companyName
        shares
        currentPrice
        totalValue
        costBasis
        returnAmount
        returnPercent
        sector
      }
      sectorAllocation
      riskMetrics
    }
  }
`;

const GET_AI_RECOMMENDATIONS = gql`
  query GetAIRecommendations($riskTolerance: String) {
    aiRecommendations(riskTolerance: $riskTolerance) {
      portfolioAnalysis {
        totalValue
        numHoldings
        sectorBreakdown
        riskScore
        diversificationScore
      }
      buyRecommendations {
        symbol
        companyName
        recommendation
        confidence
        reasoning
        targetPrice
        currentPrice
        expectedReturn
      }
      sellRecommendations {
        symbol
        companyName
        recommendation
        confidence
        reasoning
        currentPrice
        suggestedExitPrice
      }
      rebalanceSuggestions
      riskAssessment {
        overallRisk
        concentrationRisk
        sectorRisk
        volatilityEstimate
        recommendations
      }
      marketOutlook {
        overallSentiment
        confidence
        keyFactors
        risks
      }
    }
  }
`;

interface PremiumAnalyticsScreenProps {
  navigateTo: (screen: string) => void;
}

const PremiumAnalyticsScreen: React.FC<PremiumAnalyticsScreenProps> = ({ navigateTo }) => {
  const [activeTab, setActiveTab] = useState<'metrics' | 'recommendations' | 'screening'>('metrics');
  const [refreshing, setRefreshing] = useState(false);

  // Queries
  const { data: metricsData, loading: metricsLoading, refetch: refetchMetrics } = useQuery(
    GET_PREMIUM_PORTFOLIO_METRICS,
    {
      errorPolicy: 'all',
      onError: (error) => {
        if (error.message.includes('Premium subscription required')) {
          Alert.alert(
            'Premium Required',
            'This feature requires a premium subscription. Upgrade now to access advanced analytics.',
            [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Upgrade', onPress: () => navigateTo('subscription') }
            ]
          );
        }
      }
    }
  );

  const { data: recommendationsData, loading: recommendationsLoading, refetch: refetchRecommendations } = useQuery(
    GET_AI_RECOMMENDATIONS,
    {
      variables: { riskTolerance: 'medium' },
      errorPolicy: 'ignore',
      onError: (error) => {
        if (error.message.includes('Premium subscription required')) {
          Alert.alert(
            'Premium Required',
            'This feature requires a premium subscription. Upgrade now to access AI recommendations.',
            [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Upgrade', onPress: () => navigateTo('subscription') }
            ]
          );
        }
      }
    }
  );

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refetchMetrics(),
        refetchRecommendations()
      ]);
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const renderMetricsTab = () => {
    if (metricsLoading) {
      return (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading advanced metrics...</Text>
        </View>
      );
    }

    const metrics = metricsData?.premiumPortfolioMetrics;
    if (!metrics) {
      return (
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#FF3B30" />
          <Text style={styles.errorText}>Unable to load portfolio metrics</Text>
        </View>
      );
    }

    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        {/* Performance Overview */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Performance Overview</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Total Value</Text>
              <Text style={styles.metricValue}>
                ${metrics.totalValue?.toLocaleString() || '0.00'}
              </Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Total Return</Text>
              <Text style={[
                styles.metricValue,
                { color: metrics.totalReturn >= 0 ? '#34C759' : '#FF3B30' }
              ]}>
                {metrics.totalReturnPercent?.toFixed(2) || '0.00'}%
              </Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Volatility</Text>
              <Text style={styles.metricValue}>
                {metrics.volatility?.toFixed(1) || '0.0'}%
              </Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Sharpe Ratio</Text>
              <Text style={styles.metricValue}>
                {metrics.sharpeRatio?.toFixed(2) || '0.00'}
              </Text>
            </View>
          </View>
        </View>

        {/* Risk Metrics */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Risk Analysis</Text>
          <View style={styles.riskContainer}>
            <View style={styles.riskItem}>
              <Text style={styles.riskLabel}>Max Drawdown</Text>
              <Text style={styles.riskValue}>
                {metrics.maxDrawdown?.toFixed(1) || '0.0'}%
              </Text>
            </View>
            <View style={styles.riskItem}>
              <Text style={styles.riskLabel}>Beta</Text>
              <Text style={styles.riskValue}>
                {metrics.beta?.toFixed(2) || '0.00'}
              </Text>
            </View>
            <View style={styles.riskItem}>
              <Text style={styles.riskLabel}>Alpha</Text>
              <Text style={styles.riskValue}>
                {metrics.alpha?.toFixed(2) || '0.00'}
              </Text>
            </View>
          </View>
        </View>

        {/* Sector Allocation */}
        {metrics.sectorAllocation && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Sector Allocation</Text>
            <View style={styles.sectorContainer}>
              {Object.entries(metrics.sectorAllocation).map(([sector, percentage]) => (
                <View key={sector} style={styles.sectorItem}>
                  <View style={styles.sectorHeader}>
                    <Text style={styles.sectorName}>{sector}</Text>
                    <Text style={styles.sectorPercentage}>
                      {Number(percentage).toFixed(1)}%
                    </Text>
                  </View>
                  <View style={styles.progressBar}>
                    <View 
                      style={[
                        styles.progressFill, 
                        { width: `${Number(percentage)}%` }
                      ]} 
                    />
                  </View>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Holdings Details */}
        {metrics.holdings && metrics.holdings.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Holdings Analysis</Text>
            {metrics.holdings.map((holding: any, index: number) => (
              <View key={index} style={styles.holdingCard}>
                <View style={styles.holdingHeader}>
                  <Text style={styles.holdingSymbol}>{holding.symbol}</Text>
                  <Text style={[
                    styles.holdingReturn,
                    { color: holding.returnPercent >= 0 ? '#34C759' : '#FF3B30' }
                  ]}>
                    {holding.returnPercent?.toFixed(2)}%
                  </Text>
                </View>
                <Text style={styles.holdingName}>{holding.companyName}</Text>
                <View style={styles.holdingDetails}>
                  <Text style={styles.holdingDetail}>
                    {holding.shares} shares @ ${holding.currentPrice?.toFixed(2)}
                  </Text>
                  <Text style={styles.holdingDetail}>
                    Value: ${holding.totalValue?.toLocaleString()}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    );
  };

  const renderRecommendationsTab = () => {
    if (recommendationsLoading) {
      return (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading AI recommendations...</Text>
        </View>
      );
    }

    const recommendations = recommendationsData?.aiRecommendations;
    if (!recommendations) {
      return (
        <View style={styles.errorContainer}>
          <Icon name="cpu" size={48} color="#007AFF" />
          <Text style={styles.errorText}>Unable to load AI recommendations</Text>
        </View>
      );
    }

    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        {/* Market Outlook */}
        {recommendations.marketOutlook && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Market Outlook</Text>
            <View style={styles.outlookCard}>
              <View style={styles.outlookHeader}>
                <Text style={styles.outlookSentiment}>
                  {recommendations.marketOutlook.overallSentiment}
                </Text>
                <Text style={styles.outlookConfidence}>
                  {Math.round(recommendations.marketOutlook.confidence * 100)}% confidence
                </Text>
              </View>
              <View style={styles.factorsContainer}>
                <Text style={styles.factorsTitle}>Key Factors:</Text>
                {recommendations.marketOutlook.keyFactors?.map((factor: string, index: number) => (
                  <Text key={index} style={styles.factorItem}>• {factor}</Text>
                ))}
              </View>
            </View>
          </View>
        )}

        {/* Buy Recommendations */}
        {recommendations.buyRecommendations && recommendations.buyRecommendations.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Buy Recommendations</Text>
            {recommendations.buyRecommendations.map((rec: any, index: number) => (
              <View key={index} style={styles.recommendationCard}>
                <View style={styles.recommendationHeader}>
                  <Text style={styles.recommendationSymbol}>{rec.symbol}</Text>
                  <View style={styles.recommendationBadge}>
                    <Text style={styles.recommendationText}>{rec.recommendation}</Text>
                  </View>
                </View>
                <Text style={styles.recommendationName}>{rec.companyName}</Text>
                <Text style={styles.recommendationReasoning}>{rec.reasoning}</Text>
                <View style={styles.recommendationMetrics}>
                  <Text style={styles.recommendationMetric}>
                    Confidence: {Math.round(rec.confidence * 100)}%
                  </Text>
                  <Text style={styles.recommendationMetric}>
                    Expected Return: {rec.expectedReturn}%
                  </Text>
                  <Text style={styles.recommendationMetric}>
                    Target: ${rec.targetPrice}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Risk Assessment */}
        {recommendations.riskAssessment && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Risk Assessment</Text>
            <View style={styles.riskAssessmentCard}>
              <View style={styles.riskAssessmentItem}>
                <Text style={styles.riskAssessmentLabel}>Overall Risk</Text>
                <Text style={styles.riskAssessmentValue}>
                  {recommendations.riskAssessment.overallRisk}
                </Text>
              </View>
              <View style={styles.riskAssessmentItem}>
                <Text style={styles.riskAssessmentLabel}>Volatility Estimate</Text>
                <Text style={styles.riskAssessmentValue}>
                  {recommendations.riskAssessment.volatilityEstimate}%
                </Text>
              </View>
              {recommendations.riskAssessment.recommendations && (
                <View style={styles.recommendationsContainer}>
                  <Text style={styles.recommendationsTitle}>Recommendations:</Text>
                  {recommendations.riskAssessment.recommendations.map((rec: string, index: number) => (
                    <Text key={index} style={styles.recommendationItem}>• {rec}</Text>
                  ))}
                </View>
              )}
            </View>
          </View>
        )}
      </ScrollView>
    );
  };

  const renderScreeningTab = () => {
    return (
      <View style={styles.tabContent}>
        <View style={styles.comingSoonContainer}>
          <Icon name="search" size={64} color="#007AFF" />
          <Text style={styles.comingSoonTitle}>Advanced Stock Screening</Text>
          <Text style={styles.comingSoonText}>
            Coming soon! Filter stocks by sector, market cap, P/E ratio, and more.
          </Text>
          <TouchableOpacity 
            style={styles.comingSoonButton}
            onPress={() => Alert.alert('Coming Soon', 'Advanced screening will be available in the next update!')}
          >
            <Text style={styles.comingSoonButtonText}>Notify Me</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigateTo('portfolio-management')}>
          <Icon name="arrow-left" size={24} color="#000" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Premium Analytics</Text>
        <TouchableOpacity onPress={() => navigateTo('subscription')}>
          <Icon name="star" size={24} color="#FFD700" />
        </TouchableOpacity>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabNavigation}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'metrics' && styles.activeTab]}
          onPress={() => setActiveTab('metrics')}
        >
          <Text style={[styles.tabText, activeTab === 'metrics' && styles.activeTabText]}>
            Metrics
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'recommendations' && styles.activeTab]}
          onPress={() => setActiveTab('recommendations')}
        >
          <Text style={[styles.tabText, activeTab === 'recommendations' && styles.activeTabText]}>
            AI Insights
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'screening' && styles.activeTab]}
          onPress={() => setActiveTab('screening')}
        >
          <Text style={[styles.tabText, activeTab === 'screening' && styles.activeTabText]}>
            Screening
          </Text>
        </TouchableOpacity>
      </View>

      {/* Tab Content */}
      <View style={styles.tabContentContainer}>
        {activeTab === 'metrics' && renderMetricsTab()}
        {activeTab === 'recommendations' && renderRecommendationsTab()}
        {activeTab === 'screening' && renderScreeningTab()}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: '#007AFF',
  },
  tabText: {
    fontSize: 16,
    color: '#8E8E93',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  tabContentContainer: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
    padding: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 16,
    textAlign: 'center',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#000',
    marginBottom: 16,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricCard: {
    width: (width - 60) / 2,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  metricLabel: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  riskContainer: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  riskItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F2F2F7',
  },
  riskLabel: {
    fontSize: 16,
    color: '#000',
  },
  riskValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  sectorContainer: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectorItem: {
    marginBottom: 16,
  },
  sectorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  sectorName: {
    fontSize: 16,
    color: '#000',
    fontWeight: '500',
  },
  sectorPercentage: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#F2F2F7',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 4,
  },
  holdingCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  holdingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  holdingSymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  holdingReturn: {
    fontSize: 16,
    fontWeight: '600',
  },
  holdingName: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 8,
  },
  holdingDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  holdingDetail: {
    fontSize: 14,
    color: '#8E8E93',
  },
  outlookCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  outlookHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  outlookSentiment: {
    fontSize: 20,
    fontWeight: '600',
    color: '#34C759',
  },
  outlookConfidence: {
    fontSize: 14,
    color: '#8E8E93',
  },
  factorsContainer: {
    marginTop: 8,
  },
  factorsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  factorItem: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  recommendationCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  recommendationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  recommendationSymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  recommendationBadge: {
    backgroundColor: '#34C759',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  recommendationText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  recommendationName: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 8,
  },
  recommendationReasoning: {
    fontSize: 14,
    color: '#000',
    marginBottom: 12,
    lineHeight: 20,
  },
  recommendationMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  recommendationMetric: {
    fontSize: 12,
    color: '#8E8E93',
  },
  riskAssessmentCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  riskAssessmentItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F2F2F7',
  },
  riskAssessmentLabel: {
    fontSize: 16,
    color: '#000',
  },
  riskAssessmentValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF3B30',
  },
  recommendationsContainer: {
    marginTop: 16,
  },
  recommendationsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  recommendationItem: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  comingSoonContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  comingSoonTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: '#000',
    marginTop: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  comingSoonText: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  comingSoonButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 8,
  },
  comingSoonButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});

export default PremiumAnalyticsScreen;
