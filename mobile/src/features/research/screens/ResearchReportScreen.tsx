/**
 * Research Report Screen
 * Displays automated research reports for stocks
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Share,
} from 'react-native';
import { useQuery, useMutation, gql } from '@apollo/client';
import { Ionicons } from '@expo/vector-icons';
import { useRoute, useNavigation } from '@react-navigation/native';
import logger from '../../../utils/logger';

const GET_RESEARCH_REPORT = gql`
  query GetResearchReport($symbol: String!, $reportType: String) {
    researchReport(symbol: $symbol, reportType: $reportType)
  }
`;

const GENERATE_RESEARCH_REPORT = gql`
  mutation GenerateResearchReport($symbol: String!, $reportType: String, $sendEmail: Boolean) {
    generateResearchReport(symbol: $symbol, reportType: $reportType, sendEmail: $sendEmail) {
      success
      message
      report
    }
  }
`;

type RouteParams = {
  symbol: string;
};

export default function ResearchReportScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { symbol } = (route.params as RouteParams) || { symbol: '' };
  const [reportType, setReportType] = useState<'quick' | 'comprehensive' | 'deep_dive'>('comprehensive');

  const { data, loading, error, refetch } = useQuery(GET_RESEARCH_REPORT, {
    variables: { 
      symbol: symbol?.toUpperCase() || '', 
      reportType: reportType || 'comprehensive' 
    },
    skip: !symbol,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all', // Continue even if there are errors
    notifyOnNetworkStatusChange: true,
    context: {
      // Increase timeout for this specific query
      timeout: 45000, // 45 seconds for research report generation
    },
  });

  const [generateReport, { loading: generating }] = useMutation(GENERATE_RESEARCH_REPORT);

  // Parse the report with better error handling (handles both single and double-encoded JSON)
  let report = null;
  if (data?.researchReport) {
    try {
      let rawReport = data.researchReport;
      
      // Handle string - parse it
      if (typeof rawReport === 'string') {
        rawReport = JSON.parse(rawReport);
      }
      
      // If it's still a string after first parse, parse again (double-encoded)
      if (typeof rawReport === 'string') {
        report = JSON.parse(rawReport);
      } else {
        report = rawReport;
      }
      
      // Report parsed successfully
    } catch (parseError) {
      logger.error('❌ Error parsing report:', parseError);
    }
  }

  const handleGenerateReport = async () => {
    try {
      const result = await generateReport({
        variables: { symbol, reportType, sendEmail: false },
      });
      if (result.data?.generateResearchReport?.success) {
        Alert.alert('Success', result.data.generateResearchReport.message);
        // Parse the report if it's a JSON string
        if (result.data.generateResearchReport.report) {
          try {
            const parsedReport = typeof result.data.generateResearchReport.report === 'string' 
              ? JSON.parse(result.data.generateResearchReport.report) 
              : result.data.generateResearchReport.report;
            // Report generated successfully
          } catch (parseError) {
            logger.warn('⚠️ Could not parse report:', parseError);
          }
        }
        // Refetch to update the UI with the new report
        refetch();
      } else {
        Alert.alert('Error', result.data?.generateResearchReport?.message || 'Failed to generate report');
      }
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to generate report');
    }
  };

  const handleShare = async () => {
    if (!report) return;
    try {
      await Share.share({
        message: `Research Report for ${symbol}\n\n${report.executive_summary}`,
        title: `Research Report: ${symbol}`,
      });
    } catch (err) {
      logger.error('Error sharing:', err);
    }
  };

  // Show loading state
  if (loading || generating) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Generating report...</Text>
        <Text style={[styles.loadingText, { fontSize: 12, marginTop: 8, color: '#666' }]}>
          This may take up to 45 seconds...
        </Text>
      </View>
    );
  }

  if (error) {
    // Log detailed error information
    logger.error('Research Report Error:', {
      message: error.message,
      graphQLErrors: error.graphQLErrors,
      networkError: error.networkError,
      extraInfo: error.extraInfo,
    });
    
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle" size={48} color="#EF4444" />
        <Text style={styles.errorText}>Error loading report</Text>
        <Text style={styles.errorDetailText}>
          {error.message || 'Unknown error occurred'}
        </Text>
        {error.networkError && (
          <Text style={styles.errorDetailText}>
            Network: {error.networkError.message || 'Network error'}
          </Text>
        )}
        {error.graphQLErrors && error.graphQLErrors.length > 0 && (
          <Text style={styles.errorDetailText}>
            GraphQL: {error.graphQLErrors[0].message}
          </Text>
        )}
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!report) {
    // No report parsed
    
    return (
      <View style={styles.emptyContainer}>
        <Ionicons name="document-text" size={64} color="#9CA3AF" />
        <Text style={styles.emptyText}>No report available</Text>
        <Text style={styles.errorDetailText}>
          {data?.researchReport 
            ? 'Report data exists but failed to parse. Check console for details.' 
            : 'No report data in response. Try generating a new report.'}
        </Text>
        {data?.researchReport && (
          <TouchableOpacity style={styles.retryButton} onPress={() => {
            Alert.alert('Debug Info', `Report type: ${typeof data.researchReport}\nLength: ${typeof data.researchReport === 'string' ? data.researchReport.length : 'N/A'}`);
          }}>
            <Text style={styles.retryButtonText}>Show Debug Info</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity style={styles.generateButton} onPress={handleGenerateReport}>
          <Text style={styles.generateButtonText}>Generate Report</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Report structure validated

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.symbol}>{symbol}</Text>
          <Text style={styles.companyName}>
            {report?.company_name || symbol}
          </Text>
        </View>
        <TouchableOpacity onPress={handleShare}>
          <Ionicons name="share-outline" size={24} color="#007AFF" />
        </TouchableOpacity>
      </View>

      {/* Executive Summary */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Executive Summary</Text>
        <Text style={styles.summaryText}>
          {report?.executive_summary || 'No executive summary available.'}
        </Text>
      </View>

      {/* Key Metrics */}
      {report.key_metrics && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Key Metrics</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Price</Text>
              <Text style={styles.metricValue}>
                ${report.key_metrics.price?.toFixed(2) || 'N/A'}
              </Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Consumer Strength</Text>
              <Text style={styles.metricValue}>
                {report.key_metrics.consumer_strength?.toFixed(1) || 'N/A'}/100
              </Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>P/E Ratio</Text>
              <Text style={styles.metricValue}>
                {report.key_metrics.pe_ratio?.toFixed(2) || 'N/A'}
              </Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Volatility</Text>
              <Text style={styles.metricValue}>
                {report.key_metrics.volatility?.toFixed(1) || 'N/A'}%
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* Recommendation */}
      {report.sections?.recommendation && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recommendation</Text>
          <View style={styles.recommendationCard}>
            <View style={styles.recommendationHeader}>
              <Text style={styles.recommendationAction}>
                {report.sections.recommendation.action}
              </Text>
              <Text style={styles.recommendationConfidence}>
                {report.sections.recommendation.confidence?.toFixed(0)}% confidence
              </Text>
            </View>
            <Text style={styles.recommendationReasoning}>
              {report.sections.recommendation.reasoning}
            </Text>
          </View>
        </View>
      )}

      {/* Consumer Strength */}
      {report.sections?.consumer_strength && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Consumer Strength Analysis</Text>
          <View style={styles.strengthCard}>
            <Text style={styles.strengthScore}>
              {report.sections.consumer_strength.overall_score?.toFixed(1)}/100
            </Text>
            <Text style={styles.strengthTrend}>
              Trend: {report.sections.consumer_strength.historical_trend}
            </Text>
            <Text style={styles.strengthInterpretation}>
              {report.sections.consumer_strength.interpretation}
            </Text>
          </View>
        </View>
      )}

      {/* Risk Assessment */}
      {report.sections?.risk_assessment && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Risk Assessment</Text>
          <View style={styles.riskCard}>
            <Text style={styles.riskLevel}>
              {report.sections.risk_assessment.overall_risk} Risk
            </Text>
            {report.sections.risk_assessment.recommendations && (
              <View style={styles.recommendationsList}>
                {report.sections.risk_assessment.recommendations.map((rec: string, idx: number) => (
                  <Text key={idx} style={styles.recommendationItem}>
                    • {rec}
                  </Text>
                ))}
              </View>
            )}
          </View>
        </View>
      )}

      {/* Generate New Report Button */}
      <TouchableOpacity style={styles.generateButton} onPress={handleGenerateReport}>
        <Ionicons name="refresh" size={20} color="#FFFFFF" />
        <Text style={styles.generateButtonText}>Regenerate Report</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#6B7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    marginTop: 12,
    fontSize: 16,
    color: '#EF4444',
    fontWeight: 'bold',
  },
  errorDetailText: {
    marginTop: 8,
    fontSize: 12,
    color: '#EF4444',
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  retryButton: {
    marginTop: 20,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    marginTop: 16,
    fontSize: 16,
    color: '#9CA3AF',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  symbol: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  companyName: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 4,
  },
  section: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    marginTop: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 12,
  },
  summaryText: {
    fontSize: 16,
    lineHeight: 24,
    color: '#374151',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 12,
  },
  metricCard: {
    width: '48%',
    padding: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    marginRight: '2%',
    marginBottom: 12,
  },
  metricLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
  },
  recommendationCard: {
    padding: 16,
    backgroundColor: '#F0FDF4',
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#10B981',
  },
  recommendationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  recommendationAction: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#10B981',
  },
  recommendationConfidence: {
    fontSize: 14,
    color: '#6B7280',
  },
  recommendationReasoning: {
    fontSize: 16,
    lineHeight: 24,
    color: '#374151',
  },
  strengthCard: {
    padding: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
  },
  strengthScore: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 8,
  },
  strengthTrend: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  strengthInterpretation: {
    fontSize: 16,
    lineHeight: 24,
    color: '#374151',
  },
  riskCard: {
    padding: 16,
    backgroundColor: '#FEF2F2',
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#EF4444',
  },
  riskLevel: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#EF4444',
    marginBottom: 12,
  },
  recommendationsList: {
    marginTop: 8,
  },
  recommendationItem: {
    fontSize: 14,
    lineHeight: 20,
    color: '#374151',
    marginBottom: 4,
  },
  generateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    margin: 20,
    padding: 16,
    backgroundColor: '#007AFF',
    borderRadius: 12,
  },
  generateButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
});

