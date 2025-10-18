/**
 * Scan Playbook Screen
 * Detailed view of a specific scan with results and playbook information
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

import AIScansService from '../services/AIScansService';
import { AIScan, ScanResult } from '../types/AIScansTypes';

const GET_SCAN_DETAILS = gql`
  query GetScanDetails($scanId: String!) {
    scan(id: $scanId) {
      id
      name
      description
      category
      riskLevel
      timeHorizon
      isActive
      lastRun
      results {
        id
        symbol
        name
        currentPrice
        change
        changePercent
        score
        confidence
        reasoning
        riskFactors
        opportunityFactors
        technicalSignals
        fundamentalMetrics
        altDataSignals
      }
      playbook {
        id
        name
        description
        author
        performance {
          successRate
          averageReturn
          sharpeRatio
        }
      }
    }
  }
`;

interface ScanPlaybookScreenProps {
  navigation: any;
  route: {
    params: {
      scan: AIScan;
    };
  };
}

const ScanPlaybookScreen: React.FC<ScanPlaybookScreenProps> = ({ navigation, route }) => {
  const { scan } = route.params;
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(false);

  // Skip GraphQL query for now since we're using mock data
  // const { data, loading: queryLoading, refetch } = useQuery(GET_SCAN_DETAILS, {
  //   variables: { scanId: scan.id },
  //   errorPolicy: 'all',
  // });
  const data = null; // No additional data needed since we have scan from params
  const queryLoading = false;
  const refetch = async () => {}; // No-op for now

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch();
    } finally {
      setRefreshing(false);
    }
  }, [refetch]);

  const handleRunScan = useCallback(async () => {
    try {
      setLoading(true);
      const results = await AIScansService.runScan({ scanId: scan.id });
      Alert.alert('Scan Complete', `Found ${results.length} opportunities`);
      await refetch();
    } catch (error) {
      Alert.alert('Error', 'Failed to run scan');
    } finally {
      setLoading(false);
    }
  }, [scan.id, refetch]);

  const renderResultItem = (result: ScanResult) => (
    <View key={result.id} style={styles.resultCard}>
      <View style={styles.resultHeader}>
        <Text style={styles.resultSymbol}>{result.symbol}</Text>
        <View style={styles.scoreBadge}>
          <Text style={styles.scoreText}>{result.score.toFixed(1)}</Text>
        </View>
      </View>
      
      <Text style={styles.resultName}>{result.name}</Text>
      
      <View style={styles.resultMetrics}>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Price</Text>
          <Text style={styles.metricValue}>${result.currentPrice.toFixed(2)}</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Change</Text>
          <Text style={[
            styles.metricValue,
            { color: result.change >= 0 ? '#00cc99' : '#FF3B30' }
          ]}>
            {result.change >= 0 ? '+' : ''}{result.changePercent.toFixed(2)}%
          </Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Confidence</Text>
          <Text style={styles.metricValue}>
            {Math.round(result.confidence * 100)}%
          </Text>
        </View>
      </View>

      <Text style={styles.reasoning}>{result.reasoning}</Text>

      {result.opportunityFactors.length > 0 && (
        <View style={styles.factorsContainer}>
          <Text style={styles.factorsTitle}>Opportunity Factors:</Text>
          {result.opportunityFactors.map((factor, index) => (
            <Text key={index} style={styles.factorText}>• {factor}</Text>
          ))}
        </View>
      )}

      {result.riskFactors.length > 0 && (
        <View style={styles.factorsContainer}>
          <Text style={styles.factorsTitle}>Risk Factors:</Text>
          {result.riskFactors.map((factor, index) => (
            <Text key={index} style={[styles.factorText, { color: '#FF3B30' }]}>• {factor}</Text>
          ))}
        </View>
      )}
    </View>
  );

  const renderPlaybookInfo = () => {
    if (!scan.playbook) return null;

    return (
      <View style={styles.playbookCard}>
        <Text style={styles.playbookTitle}>Based on Playbook</Text>
        <Text style={styles.playbookName}>{scan.playbook.name}</Text>
        <Text style={styles.playbookDescription}>{scan.playbook.description}</Text>
        
        <View style={styles.playbookMetrics}>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Success Rate</Text>
            <Text style={styles.metricValue}>
              {Math.round(scan.playbook.performance.successRate * 100)}%
            </Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Avg Return</Text>
            <Text style={styles.metricValue}>
              {(scan.playbook.performance.averageReturn * 100).toFixed(1)}%
            </Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Sharpe Ratio</Text>
            <Text style={styles.metricValue}>
              {scan.playbook.performance.sharpeRatio.toFixed(2)}
            </Text>
          </View>
        </View>
      </View>
    );
  };

  if (queryLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#00cc99" />
        <Text style={styles.loadingText}>Loading scan details...</Text>
      </View>
    );
  }

  const scanData = data?.scan || scan;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Icon name="arrow-left" size={24} color="#000" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{scanData.name || 'Untitled Scan'}</Text>
        <TouchableOpacity
          style={[styles.runButton, loading && styles.runButtonDisabled]}
          onPress={handleRunScan}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Icon name="play" size={20} color="#fff" />
          )}
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Scan Info */}
        <View style={styles.infoCard}>
          <Text style={styles.description}>{scanData.description || 'No description available'}</Text>
          
          <View style={styles.metrics}>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Category</Text>
              <Text style={styles.metricValue}>
                {scanData.category ? scanData.category.charAt(0).toUpperCase() + scanData.category.slice(1) : 'Unknown'}
              </Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Risk Level</Text>
              <Text style={styles.metricValue}>
                {scanData.riskLevel ? scanData.riskLevel.charAt(0).toUpperCase() + scanData.riskLevel.slice(1) : 'Unknown'}
              </Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Time Horizon</Text>
              <Text style={styles.metricValue}>
                {scanData.timeHorizon ? scanData.timeHorizon.charAt(0).toUpperCase() + scanData.timeHorizon.slice(1) : 'Unknown'}
              </Text>
            </View>
          </View>
        </View>

        {/* Playbook Info */}
        {renderPlaybookInfo()}

        {/* Results */}
        <View style={styles.resultsSection}>
          <Text style={styles.resultsTitle}>
            Latest Results ({scanData.results?.length || 0} opportunities)
          </Text>
          
          {scanData.results && scanData.results.length > 0 ? (
            scanData.results.map(renderResultItem)
          ) : (
            <View style={styles.noResultsContainer}>
              <Icon name="search" size={48} color="#8E8E93" />
              <Text style={styles.noResultsTitle}>No Results Yet</Text>
              <Text style={styles.noResultsText}>
                Run the scan to find market opportunities
              </Text>
              <TouchableOpacity
                style={styles.runScanButton}
                onPress={handleRunScan}
                disabled={loading}
              >
                <Icon name="play" size={20} color="#fff" />
                <Text style={styles.runScanButtonText}>Run Scan</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    flex: 1,
    textAlign: 'center',
  },
  runButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#00cc99',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  runButtonDisabled: {
    backgroundColor: '#8E8E93',
  },
  content: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#8E8E93',
  },
  infoCard: {
    backgroundColor: '#F2F2F7',
    margin: 16,
    padding: 16,
    borderRadius: 12,
  },
  description: {
    fontSize: 16,
    color: '#8E8E93',
    marginBottom: 16,
    lineHeight: 22,
  },
  metrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#000',
  },
  playbookCard: {
    backgroundColor: '#E8F5E8',
    margin: 16,
    marginTop: 0,
    padding: 16,
    borderRadius: 12,
  },
  playbookTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#00cc99',
    marginBottom: 4,
  },
  playbookName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  playbookDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 12,
  },
  playbookMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  resultsSection: {
    padding: 16,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginBottom: 16,
  },
  resultCard: {
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  resultSymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  scoreBadge: {
    backgroundColor: '#00cc99',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  scoreText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  resultName: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 12,
  },
  resultMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  reasoning: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 12,
    lineHeight: 20,
  },
  factorsContainer: {
    marginBottom: 8,
  },
  factorsTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  factorText: {
    fontSize: 12,
    color: '#00cc99',
    marginBottom: 2,
  },
  noResultsContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  noResultsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginTop: 16,
    marginBottom: 8,
  },
  noResultsText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginBottom: 24,
  },
  runScanButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#00cc99',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  runScanButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginLeft: 8,
  },
});

export default ScanPlaybookScreen;
