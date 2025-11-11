/**
 * Sentry Test Button Component
 * Allows testing Sentry error tracking in development
 */
import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet, Alert } from 'react-native';
import Sentry from '../config/sentry';

interface SentryTestButtonProps {
  style?: any;
}

export default function SentryTestButton({ style }: SentryTestButtonProps) {
  const testError = () => {
    try {
      // Test 1: Capture a simple error
      Sentry.captureException(new Error('Sentry Test Error - This is a test error to verify Sentry integration'));
      
      // Test 2: Capture a message
      Sentry.captureMessage('Sentry Test Message - Testing error tracking', 'info');
      
      // Test 3: Add context
      Sentry.setContext('test', {
        testType: 'manual',
        timestamp: new Date().toISOString(),
        environment: 'development',
      });
      
      Alert.alert(
        'Sentry Test Sent',
        'Test error and message sent to Sentry. Check your Sentry dashboard to verify.',
        [{ text: 'OK' }]
      );
    } catch (error) {
      Alert.alert('Error', `Failed to send test error: ${error}`);
    }
  };

  const testCrash = () => {
    Alert.alert(
      '⚠️ Warning',
      'This will crash the app to test native crash reporting. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Crash',
          style: 'destructive',
          onPress: () => {
            // This will cause a native crash
            throw new Error('Sentry Test Crash - Testing native crash reporting');
          },
        },
      ]
    );
  };

  const testPerformance = () => {
    const transaction = Sentry.startTransaction({
      name: 'Test Transaction',
      op: 'test',
    });

    // Simulate some work
    setTimeout(() => {
      transaction.finish();
      Alert.alert('Performance Test', 'Performance transaction sent to Sentry');
    }, 100);
  };

  return (
    <View style={[styles.container, style]}>
      <Text style={styles.title}>Sentry Test Tools</Text>
      
      <TouchableOpacity style={styles.button} onPress={testError}>
        <Text style={styles.buttonText}>Test Error & Message</Text>
      </TouchableOpacity>

      <TouchableOpacity style={[styles.button, styles.performanceButton]} onPress={testPerformance}>
        <Text style={styles.buttonText}>Test Performance</Text>
      </TouchableOpacity>

      <TouchableOpacity style={[styles.button, styles.crashButton]} onPress={testCrash}>
        <Text style={styles.buttonText}>Test Crash (⚠️)</Text>
      </TouchableOpacity>

      <Text style={styles.note}>
        Note: These tests will send data to Sentry. Use only in development.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    margin: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#333',
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 12,
    borderRadius: 6,
    marginBottom: 8,
    alignItems: 'center',
  },
  performanceButton: {
    backgroundColor: '#34C759',
  },
  crashButton: {
    backgroundColor: '#FF3B30',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  note: {
    fontSize: 12,
    color: '#666',
    marginTop: 8,
    fontStyle: 'italic',
  },
});

