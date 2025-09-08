import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  Switch
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import MarketDataService from '../services/MarketDataService';

interface MarketDataConfigProps {
  onClose: () => void;
}

const MarketDataConfig: React.FC<MarketDataConfigProps> = ({ onClose }) => {
  const [apiKey, setApiKey] = useState('');
  const [isRealDataEnabled, setIsRealDataEnabled] = useState(false);
  const [testSymbol, setTestSymbol] = useState('AAPL');
  const [testResult, setTestResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadCurrentSettings();
  }, []);

  const loadCurrentSettings = async () => {
    try {
      const storedKey = await AsyncStorage.getItem('alpha_vantage_api_key');
      const realDataEnabled = await AsyncStorage.getItem('real_market_data_enabled');
      
      if (storedKey) {
        setApiKey(storedKey);
      }
      setIsRealDataEnabled(realDataEnabled === 'true');
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveApiKey = async () => {
    if (!apiKey.trim()) {
      Alert.alert('Error', 'Please enter a valid API key');
      return;
    }

    try {
      await MarketDataService.setApiKey(apiKey.trim());
      await AsyncStorage.setItem('real_market_data_enabled', 'true');
      setIsRealDataEnabled(true);
      Alert.alert('Success', 'API key saved successfully!');
    } catch (error) {
      Alert.alert('Error', 'Failed to save API key');
    }
  };

  const toggleRealData = async (enabled: boolean) => {
    try {
      await AsyncStorage.setItem('real_market_data_enabled', enabled.toString());
      setIsRealDataEnabled(enabled);
      
      if (enabled && !apiKey) {
        Alert.alert(
          'API Key Required',
          'To enable real market data, you need to provide an Alpha Vantage API key. You can get a free key at alphavantage.co',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Get API Key', onPress: () => {} }
          ]
        );
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to update settings');
    }
  };

  const testApiConnection = async () => {
    if (!apiKey.trim()) {
      Alert.alert('Error', 'Please enter an API key first');
      return;
    }

    setIsLoading(true);
    try {
      await MarketDataService.setApiKey(apiKey.trim());
      const quote = await MarketDataService.getStockQuote(testSymbol);
      setTestResult(quote);
      Alert.alert('Success', `Successfully fetched data for ${testSymbol}`);
    } catch (error) {
      Alert.alert('Error', `Failed to fetch data: ${error.message}`);
      setTestResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  const getApiKeyInstructions = () => {
    Alert.alert(
      'How to Get Alpha Vantage API Key',
      '1. Go to alphavantage.co\n2. Click "Get Free API Key"\n3. Fill out the form\n4. Copy your API key\n5. Paste it here\n\nFree tier includes:\n- 5 API calls per minute\n- 500 calls per day\n- Real-time and historical data',
      [{ text: 'Got it!' }]
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Market Data Configuration</Text>
        <TouchableOpacity onPress={onClose} style={styles.closeButton}>
          <Text style={styles.closeButtonText}>✕</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Real Market Data</Text>
        <View style={styles.switchContainer}>
          <Text style={styles.switchLabel}>Enable Real Market Data</Text>
          <Switch
            value={isRealDataEnabled}
            onValueChange={toggleRealData}
            trackColor={{ false: '#767577', true: '#81b0ff' }}
            thumbColor={isRealDataEnabled ? '#f5dd4b' : '#f4f3f4'}
          />
        </View>
        <Text style={styles.description}>
          When enabled, the app will fetch real stock prices, market data, and news from Alpha Vantage API.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Alpha Vantage API Key</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter your Alpha Vantage API key"
          value={apiKey}
          onChangeText={setApiKey}
          secureTextEntry
          autoCapitalize="none"
        />
        <TouchableOpacity onPress={getApiKeyInstructions} style={styles.helpButton}>
          <Text style={styles.helpButtonText}>How to get API key?</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={saveApiKey} style={styles.saveButton}>
          <Text style={styles.saveButtonText}>Save API Key</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Test Connection</Text>
        <View style={styles.testContainer}>
          <TextInput
            style={[styles.input, styles.testInput]}
            placeholder="Symbol (e.g., AAPL)"
            value={testSymbol}
            onChangeText={setTestSymbol}
            autoCapitalize="characters"
          />
          <TouchableOpacity 
            onPress={testApiConnection} 
            style={[styles.testButton, isLoading && styles.testButtonDisabled]}
            disabled={isLoading}
          >
            <Text style={styles.testButtonText}>
              {isLoading ? 'Testing...' : 'Test'}
            </Text>
          </TouchableOpacity>
        </View>
        
        {testResult && (
          <View style={styles.testResult}>
            <Text style={styles.testResultTitle}>Test Result:</Text>
            <Text style={styles.testResultText}>
              Symbol: {testResult.symbol}
            </Text>
            <Text style={styles.testResultText}>
              Price: ${testResult.price.toFixed(2)}
            </Text>
            <Text style={styles.testResultText}>
              Change: {testResult.change > 0 ? '+' : ''}{testResult.change.toFixed(2)} ({testResult.changePercent.toFixed(2)}%)
            </Text>
            <Text style={styles.testResultText}>
              Volume: {testResult.volume.toLocaleString()}
            </Text>
            <Text style={styles.testResultText}>
              Market Status: {testResult.marketStatus}
            </Text>
          </View>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Features</Text>
        <View style={styles.featureList}>
          <Text style={styles.featureItem}>✅ Real-time stock prices</Text>
          <Text style={styles.featureItem}>✅ Historical data</Text>
          <Text style={styles.featureItem}>✅ Market news</Text>
          <Text style={styles.featureItem}>✅ Market hours detection</Text>
          <Text style={styles.featureItem}>✅ Stock search</Text>
          <Text style={styles.featureItem}>✅ Technical indicators</Text>
        </View>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Without an API key, the app will use mock data for demonstration purposes.
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  closeButton: {
    padding: 5,
  },
  closeButtonText: {
    fontSize: 18,
    color: '#666',
  },
  section: {
    backgroundColor: '#fff',
    margin: 10,
    padding: 15,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  switchLabel: {
    fontSize: 14,
    color: '#333',
  },
  description: {
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    backgroundColor: '#fff',
    marginBottom: 10,
  },
  helpButton: {
    alignSelf: 'flex-start',
    marginBottom: 10,
  },
  helpButtonText: {
    color: '#007AFF',
    fontSize: 12,
    textDecorationLine: 'underline',
  },
  saveButton: {
    backgroundColor: '#007AFF',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  testContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  testInput: {
    flex: 1,
    marginRight: 10,
    marginBottom: 0,
  },
  testButton: {
    backgroundColor: '#34C759',
    padding: 12,
    borderRadius: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  testButtonDisabled: {
    backgroundColor: '#ccc',
  },
  testButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  testResult: {
    backgroundColor: '#f0f8ff',
    padding: 10,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  testResultTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  testResultText: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  featureList: {
    marginTop: 5,
  },
  featureItem: {
    fontSize: 12,
    color: '#333',
    marginBottom: 3,
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    lineHeight: 16,
  },
});

export default MarketDataConfig;
