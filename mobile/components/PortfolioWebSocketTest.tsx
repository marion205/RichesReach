import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import webSocketService, { PortfolioUpdate } from '../services/WebSocketService';

interface TestResult {
  id: number;
  timestamp: string;
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  marketStatus: string;
  latency?: number;
}

export default function PortfolioWebSocketTest() {
  const [isConnected, setIsConnected] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [updateCount, setUpdateCount] = useState(0);
  const [lastUpdateTime, setLastUpdateTime] = useState<string>('');
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [isTestRunning, setIsTestRunning] = useState(false);
  
  const startTime = useRef<number>(0);
  const testStartTime = useRef<number>(0);

  useEffect(() => {
    setupWebSocket();
    return () => {
      // Cleanup handled by singleton
    };
  }, []);

  const setupWebSocket = () => {
    try {
      // Set up callbacks
      webSocketService.setCallbacks({
        onPortfolioUpdate: (portfolio: PortfolioUpdate) => {
          const now = Date.now();
          const timestamp = new Date().toLocaleTimeString();
          
          // Calculate latency if we have a start time
          const latency = startTime.current ? now - startTime.current : undefined;
          
          const result: TestResult = {
            id: updateCount + 1,
            timestamp,
            totalValue: portfolio.totalValue,
            totalReturn: portfolio.totalReturn,
            totalReturnPercent: portfolio.totalReturnPercent,
            marketStatus: portfolio.marketStatus,
            latency
          };
          
          setTestResults(prev => [result, ...prev.slice(0, 19)]); // Keep last 20 results
          setUpdateCount(prev => prev + 1);
          setLastUpdateTime(timestamp);
          
          console.log('📊 Test received update:', result);
        },
        onConnectionStatusChange: (connected: boolean) => {
          setIsConnected(connected);
          setConnectionStatus(connected ? 'Connected' : 'Disconnected');
        }
      });
      
      // Connect
      webSocketService.connect();
      
    } catch (error) {
      console.error('Error setting up WebSocket test:', error);
      Alert.alert('Error', 'Failed to setup WebSocket test');
    }
  };

  const startTest = () => {
    setIsTestRunning(true);
    setTestResults([]);
    setUpdateCount(0);
    testStartTime.current = Date.now();
    
    // Subscribe to portfolio updates
    setTimeout(() => {
      webSocketService.subscribeToPortfolio();
    }, 1000);
    
    // Auto-stop after 30 seconds
    setTimeout(() => {
      stopTest();
    }, 30000);
  };

  const stopTest = () => {
    setIsTestRunning(false);
  };

  const clearResults = () => {
    setTestResults([]);
    setUpdateCount(0);
  };

  const getConnectionColor = () => {
    if (isConnected) return '#34C759';
    if (connectionStatus === 'Connecting') return '#FF9500';
    return '#FF3B30';
  };

  const getAverageLatency = () => {
    const resultsWithLatency = testResults.filter(r => r.latency !== undefined);
    if (resultsWithLatency.length === 0) return 0;
    
    const total = resultsWithLatency.reduce((sum, r) => sum + (r.latency || 0), 0);
    return Math.round(total / resultsWithLatency.length);
  };

  const getDataConsistency = () => {
    if (testResults.length < 2) return 'N/A';
    
    const values = testResults.slice(0, 5).map(r => r.totalValue);
    const uniqueValues = new Set(values);
    
    if (uniqueValues.size === 1) return '✅ Consistent';
    return `❌ ${uniqueValues.size} different values`;
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>📊 Portfolio WebSocket Test</Text>
      
      {/* Connection Status */}
      <View style={styles.statusContainer}>
        <View style={[styles.statusIndicator, { backgroundColor: getConnectionColor() }]} />
        <Text style={styles.statusText}>
          Status: {connectionStatus}
        </Text>
      </View>
      
      {/* Test Controls */}
      <View style={styles.controlsContainer}>
        <TouchableOpacity
          style={[styles.button, isTestRunning ? styles.buttonDisabled : styles.buttonStart]}
          onPress={startTest}
          disabled={isTestRunning}
        >
          <Text style={styles.buttonText}>
            {isTestRunning ? '🔄 Testing...' : '▶️ Start Test'}
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.button, styles.buttonStop]}
          onPress={stopTest}
          disabled={!isTestRunning}
        >
          <Text style={styles.buttonText}>⏹️ Stop</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.button, styles.buttonClear]}
          onPress={clearResults}
        >
          <Text style={styles.buttonText}>🗑️ Clear</Text>
        </TouchableOpacity>
      </View>
      
      {/* Test Statistics */}
      <View style={styles.statsContainer}>
        <Text style={styles.statsTitle}>📈 Test Statistics</Text>
        <View style={styles.statsGrid}>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Updates Received</Text>
            <Text style={styles.statValue}>{updateCount}</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Avg Latency</Text>
            <Text style={styles.statValue}>{getAverageLatency()}ms</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Data Consistency</Text>
            <Text style={styles.statValue}>{getDataConsistency()}</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Last Update</Text>
            <Text style={styles.statValue}>{lastUpdateTime || 'None'}</Text>
          </View>
        </View>
      </View>
      
      {/* Test Results */}
      <View style={styles.resultsContainer}>
        <Text style={styles.resultsTitle}>📋 Recent Updates</Text>
        {testResults.length === 0 ? (
          <Text style={styles.noResults}>No updates received yet</Text>
        ) : (
          testResults.map((result) => (
            <View key={result.id} style={styles.resultItem}>
              <View style={styles.resultHeader}>
                <Text style={styles.resultId}>#{result.id}</Text>
                <Text style={styles.resultTime}>{result.timestamp}</Text>
                {result.latency && (
                  <Text style={styles.resultLatency}>{result.latency}ms</Text>
                )}
              </View>
              <View style={styles.resultData}>
                <Text style={styles.resultValue}>
                  💰 ${result.totalValue.toLocaleString('en-US', { 
                    minimumFractionDigits: 2, 
                    maximumFractionDigits: 2 
                  })}
                </Text>
                <Text style={[
                  styles.resultReturn,
                  { color: result.totalReturn >= 0 ? '#34C759' : '#FF3B30' }
                ]}>
                  📈 {result.totalReturn >= 0 ? '+' : ''}{result.totalReturnPercent.toFixed(2)}%
                </Text>
                <Text style={styles.resultStatus}>
                  🏢 {result.marketStatus}
                </Text>
              </View>
            </View>
          ))
        )}
      </View>
      
      {/* Instructions */}
      <View style={styles.instructionsContainer}>
        <Text style={styles.instructionsTitle}>📖 How to Test</Text>
        <Text style={styles.instructionsText}>
          1. Make sure your backend server is running with WebSocket support{'\n'}
          2. Tap "Start Test" to begin receiving live updates{'\n'}
          3. Watch the statistics and recent updates{'\n'}
          4. Check data consistency and latency{'\n'}
          5. The test will auto-stop after 30 seconds
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
    color: '#1C1C1E',
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  statusText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  controlsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  button: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    minWidth: 100,
    alignItems: 'center',
  },
  buttonStart: {
    backgroundColor: '#34C759',
  },
  buttonStop: {
    backgroundColor: '#FF3B30',
  },
  buttonClear: {
    backgroundColor: '#8E8E93',
  },
  buttonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  buttonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 14,
  },
  statsContainer: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#1C1C1E',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statItem: {
    width: '48%',
    marginBottom: 12,
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  resultsContainer: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#1C1C1E',
  },
  noResults: {
    textAlign: 'center',
    color: '#8E8E93',
    fontStyle: 'italic',
    padding: 20,
  },
  resultItem: {
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    paddingVertical: 12,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  resultId: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  resultTime: {
    fontSize: 12,
    color: '#8E8E93',
  },
  resultLatency: {
    fontSize: 12,
    color: '#34C759',
    fontWeight: '600',
  },
  resultData: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  resultValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  resultReturn: {
    fontSize: 14,
    fontWeight: '600',
  },
  resultStatus: {
    fontSize: 12,
    color: '#8E8E93',
  },
  instructionsContainer: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  instructionsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#1C1C1E',
  },
  instructionsText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#1C1C1E',
  },
});
