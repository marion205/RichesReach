/**
 * Performance Test Button Component
 * Add this to your app to run performance tests
 */

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { runSimplePerformanceTest } from '../utils/simplePerformanceTest';

interface PerformanceTestButtonProps {
  style?: any;
}

const PerformanceTestButton: React.FC<PerformanceTestButtonProps> = ({ style }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [lastResults, setLastResults] = useState<any>(null);

  const runFullTest = async () => {
    if (isRunning) return;
    
    setIsRunning(true);
    try {
      console.log('🚀 Starting performance test...');
      const results = await runSimplePerformanceTest();
      setLastResults(results);
      
      Alert.alert(
        'Performance Test Complete!',
        `Total Operations: ${results.totalOperations}\n` +
        `Average Time: ${results.averageTime.toFixed(2)}ms\n` +
        `Success Rate: ${results.successRate.toFixed(1)}%\n` +
        `Concurrent Time: ${results.concurrentTime.toFixed(2)}ms\n\n` +
        `Check console for detailed results!`,
        [{ text: 'OK' }]
      );
    } catch (error) {
      console.error('Performance test error:', error);
      Alert.alert('Test Error', 'Performance test failed. Check console for details.');
    } finally {
      setIsRunning(false);
    }
  };

  const runQuickTest = async () => {
    if (isRunning) return;
    
    setIsRunning(true);
    try {
      console.log('⚡ Starting quick performance test...');
      const results = await runSimplePerformanceTest();
      
      Alert.alert(
        'Quick Test Complete!',
        `Average Time: ${results.averageTime.toFixed(2)}ms\n` +
        `Success Rate: ${results.successRate.toFixed(1)}%\n\n` +
        `Check console for detailed results!`,
        [{ text: 'OK' }]
      );
    } catch (error) {
      console.error('Quick test error:', error);
      Alert.alert('Test Error', 'Quick test failed. Check console for details.');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <View style={[styles.container, style]}>
      <Text style={styles.title}>Performance Tests</Text>
      
      <TouchableOpacity
        style={[styles.button, styles.fullTestButton, isRunning && styles.disabledButton]}
        onPress={runFullTest}
        disabled={isRunning}
      >
        <Text style={styles.buttonText}>
          {isRunning ? 'Running...' : 'Run Full Test'}
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.button, styles.quickTestButton, isRunning && styles.disabledButton]}
        onPress={runQuickTest}
        disabled={isRunning}
      >
        <Text style={styles.buttonText}>
          {isRunning ? 'Running...' : 'Quick Test'}
        </Text>
      </TouchableOpacity>
      
      {lastResults && (
        <View style={styles.results}>
          <Text style={styles.resultsTitle}>Last Results:</Text>
          <Text style={styles.resultsText}>
            Average Time: {lastResults.averageTime.toFixed(2)}ms
          </Text>
          <Text style={styles.resultsText}>
            Total Operations: {lastResults.totalOperations}
          </Text>
          <Text style={styles.resultsText}>
            Success Rate: {lastResults.successRate.toFixed(1)}%
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    margin: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
    color: '#333',
  },
  button: {
    padding: 12,
    borderRadius: 6,
    marginBottom: 8,
    alignItems: 'center',
  },
  fullTestButton: {
    backgroundColor: '#007AFF',
  },
  quickTestButton: {
    backgroundColor: '#34C759',
  },
  disabledButton: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 16,
  },
  results: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#e9ecef',
    borderRadius: 6,
  },
  resultsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  resultsText: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
});

export default PerformanceTestButton;
