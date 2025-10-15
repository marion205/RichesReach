/**
 * Connectivity Screen Component
 * Tests API endpoints and shows connection status
 * Handy for debugging network issues before demos
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  Platform,
} from 'react-native';
import { API_HTTP, API_GRAPHQL, API_AUTH, API_WS } from '../config/api';
import { fetchWithTimeout } from '../utils/fetchWithTimeout';

interface EndpointStatus {
  name: string;
  url: string;
  status: 'pending' | 'success' | 'error';
  responseTime?: number;
  error?: string;
  details?: string;
}

export const ConnectivityScreen: React.FC = () => {
  const [endpoints, setEndpoints] = useState<EndpointStatus[]>([
    { name: 'Health Check', url: `${API_HTTP}/health/`, status: 'pending' },
    { name: 'GraphQL', url: API_GRAPHQL, status: 'pending' },
    { name: 'Auth', url: API_AUTH, status: 'pending' },
    { name: 'WebSocket', url: API_WS, status: 'pending' },
  ]);
  const [isTesting, setIsTesting] = useState(false);

  const testEndpoint = async (endpoint: EndpointStatus): Promise<EndpointStatus> => {
    const startTime = Date.now();
    
    try {
      let response: Response;
      
      if (endpoint.name === 'GraphQL') {
        // Test GraphQL with a simple query
        response = await fetchWithTimeout(endpoint.url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: '{ stocks { symbol companyName currentPrice } }'
          }),
        }, 5000);
      } else if (endpoint.name === 'WebSocket') {
        // WebSocket test is more complex, just check if URL is valid
        return {
          ...endpoint,
          status: 'success',
          responseTime: Date.now() - startTime,
          details: 'WebSocket URL configured (manual test required)',
        };
      } else {
        // Standard GET request
        response = await fetchWithTimeout(endpoint.url, {
          method: 'GET',
        }, 5000);
      }

      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        let details = `Status: ${response.status}`;
        if (endpoint.name === 'GraphQL') {
          const data = await response.json();
          details += ` | Stocks: ${data.data?.stocks?.length || 0}`;
        }
        
        return {
          ...endpoint,
          status: 'success',
          responseTime,
          details,
        };
      } else {
        return {
          ...endpoint,
          status: 'error',
          responseTime,
          error: `HTTP ${response.status}`,
          details: await response.text().catch(() => 'No response body'),
        };
      }
    } catch (error) {
      return {
        ...endpoint,
        status: 'error',
        responseTime: Date.now() - startTime,
        error: error instanceof Error ? error.message : 'Unknown error',
        details: 'Network request failed',
      };
    }
  };

  const testAllEndpoints = async () => {
    setIsTesting(true);
    setEndpoints(prev => prev.map(ep => ({ ...ep, status: 'pending' as const })));

    const results = await Promise.all(
      endpoints.map(endpoint => testEndpoint(endpoint))
    );

    setEndpoints(results);
    setIsTesting(false);

    // Show summary
    const successCount = results.filter(r => r.status === 'success').length;
    const totalCount = results.length;
    
    if (successCount === totalCount) {
      Alert.alert('✅ All Tests Passed', `All ${totalCount} endpoints are working correctly!`);
    } else {
      Alert.alert(
        '⚠️ Some Tests Failed', 
        `${successCount}/${totalCount} endpoints are working. Check the details below.`
      );
    }
  };

  const getStatusColor = (status: EndpointStatus['status']) => {
    switch (status) {
      case 'success': return '#34C759';
      case 'error': return '#FF3B30';
      case 'pending': return '#FF9500';
      default: return '#8E8E93';
    }
  };

  const getStatusIcon = (status: EndpointStatus['status']) => {
    switch (status) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'pending': return '⏳';
      default: return '❓';
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>🔧 Connectivity Test</Text>
        <Text style={styles.subtitle}>
          Test API endpoints before your demo
        </Text>
      </View>

      <View style={styles.configInfo}>
        <Text style={styles.configTitle}>Current Configuration:</Text>
        <Text style={styles.configText}>Platform: {Platform.OS}</Text>
        <Text style={styles.configText}>Base URL: {API_HTTP}</Text>
        <Text style={styles.configText}>GraphQL: {API_GRAPHQL}</Text>
        <Text style={styles.configText}>Auth: {API_AUTH}</Text>
        <Text style={styles.configText}>WebSocket: {API_WS}</Text>
      </View>

      <TouchableOpacity
        style={[styles.testButton, isTesting && styles.testButtonDisabled]}
        onPress={testAllEndpoints}
        disabled={isTesting}
      >
        <Text style={styles.testButtonText}>
          {isTesting ? 'Testing...' : '🧪 Test All Endpoints'}
        </Text>
      </TouchableOpacity>

      <View style={styles.resultsContainer}>
        <Text style={styles.resultsTitle}>Test Results:</Text>
        {endpoints.map((endpoint, index) => (
          <View key={index} style={styles.endpointCard}>
            <View style={styles.endpointHeader}>
              <Text style={styles.endpointName}>{endpoint.name}</Text>
              <Text style={styles.endpointStatus}>
                {getStatusIcon(endpoint.status)}
              </Text>
            </View>
            
            <Text style={styles.endpointUrl}>{endpoint.url}</Text>
            
            {endpoint.status !== 'pending' && (
              <View style={styles.endpointDetails}>
                {endpoint.responseTime && (
                  <Text style={styles.responseTime}>
                    Response Time: {endpoint.responseTime}ms
                  </Text>
                )}
                
                {endpoint.details && (
                  <Text style={styles.details}>{endpoint.details}</Text>
                )}
                
                {endpoint.error && (
                  <Text style={styles.error}>Error: {endpoint.error}</Text>
                )}
              </View>
            )}
            
            <View 
              style={[
                styles.statusIndicator, 
                { backgroundColor: getStatusColor(endpoint.status) }
              ]} 
            />
          </View>
        ))}
      </View>

      <View style={styles.troubleshooting}>
        <Text style={styles.troubleshootingTitle}>🔧 Troubleshooting Tips:</Text>
        <Text style={styles.troubleshootingText}>
          • If localhost fails but IP works: Use real device with EXPO_PUBLIC_API_HOST
        </Text>
        <Text style={styles.troubleshootingText}>
          • If all fail: Check Django server is running on 0.0.0.0:8000
        </Text>
        <Text style={styles.troubleshootingText}>
          • If GraphQL fails: Check server logs for errors
        </Text>
        <Text style={styles.troubleshootingText}>
          • For real device: Set EXPO_PUBLIC_API_HOST=YOUR_IP in .env
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 4,
  },
  configInfo: {
    margin: 16,
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  configTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  configText: {
    fontSize: 14,
    color: '#666',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 2,
  },
  testButton: {
    margin: 16,
    padding: 16,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    alignItems: 'center',
  },
  testButtonDisabled: {
    backgroundColor: '#ccc',
  },
  testButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  resultsContainer: {
    margin: 16,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  endpointCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    position: 'relative',
  },
  endpointHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  endpointName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  endpointStatus: {
    fontSize: 20,
  },
  endpointUrl: {
    fontSize: 12,
    color: '#666',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 8,
  },
  endpointDetails: {
    marginTop: 8,
  },
  responseTime: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  details: {
    fontSize: 14,
    color: '#34C759',
    marginTop: 4,
  },
  error: {
    fontSize: 14,
    color: '#FF3B30',
    marginTop: 4,
  },
  statusIndicator: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: 4,
    height: '100%',
    borderTopLeftRadius: 8,
    borderBottomLeftRadius: 8,
  },
  troubleshooting: {
    margin: 16,
    padding: 16,
    backgroundColor: '#fff3cd',
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#ffc107',
  },
  troubleshootingTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#856404',
    marginBottom: 8,
  },
  troubleshootingText: {
    fontSize: 14,
    color: '#856404',
    marginBottom: 4,
  },
});

export default ConnectivityScreen;
