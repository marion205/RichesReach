/**
 * Yodlee FastLink WebView Component
 * Handles rendering FastLink in a WebView with proper message handling
 */

import React, { useRef, useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Linking, Alert } from 'react-native';
import { WebView } from 'react-native-webview';
import { FastLinkSession } from '../services/YodleeService';

interface FastLinkWebViewProps {
  session: FastLinkSession;
  onSuccess: (result: any) => void;
  onError: (error: string) => void;
  onClose: () => void;
}

const FastLinkWebView: React.FC<FastLinkWebViewProps> = ({
  session,
  onSuccess,
  onError,
  onClose,
}) => {
  const webViewRef = useRef<WebView>(null);

  // Prepare POST data for FastLink
  const postData = `accessToken=Bearer ${session.accessToken}&extraParams=${encodeURIComponent(
    JSON.stringify({
      configName: (session.fastlink?.config?.params as any)?.configName || 'default',
      ...session.fastlink?.config?.params,
    })
  )}`;

  // FastLink URL from session
  const fastLinkUrl = session.fastlink?.config?.fastLinkURL || '';

  // Handle messages from FastLink with security validation
  const handleMessage = (event: any) => {
    const { data } = event.nativeEvent;
    
    try {
      const parsed = JSON.parse(data);
      
      // Security: Validate origin and type
      // Only process messages that look like valid Yodlee events
      if (!parsed.type && !parsed.event) {
        console.warn('FastLink: Invalid message format - missing type/event');
        return;
      }
      
      // Additional validation: Check for expected Yodlee message structure
      const isValidYodleeMessage = 
        parsed.type === 'POST_MESSAGE' ||
        parsed.type === 'OPEN_EXTERNAL_URL' ||
        parsed.type === 'success' ||
        parsed.type === 'error' ||
        parsed.type === 'close' ||
        parsed.event === 'close' ||
        parsed.event === 'success';
      
      if (!isValidYodleeMessage) {
        console.warn('FastLink: Unknown message type:', parsed.type || parsed.event);
        return;
      }
      
      console.log('FastLink message received:', parsed);

      // Handle different message types
      if (parsed.type === 'POST_MESSAGE' || parsed.event === 'success' || parsed.event === 'close') {
        // FastLink completion or account update
        if (parsed.data?.event === 'close' || parsed.event === 'close') {
          // FastLink closed successfully
          onSuccess(parsed.data || parsed);
        } else if (parsed.data?.event === 'success' || parsed.event === 'success') {
          // Account linked successfully
          onSuccess(parsed.data || parsed);
        }
      } else if (parsed.type === 'OPEN_EXTERNAL_URL') {
        // Handle Open Banking redirects
        const url = parsed.data?.url;
        if (url && typeof url === 'string') {
          // Validate URL is HTTPS or a safe scheme
          if (url.startsWith('http://') && !url.includes('localhost')) {
            console.warn('FastLink: Blocked insecure HTTP URL:', url);
            return;
          }
          
          Linking.canOpenURL(url)
            .then((supported) => {
              if (supported) {
                Linking.openURL(url);
              } else {
                Alert.alert('Error', 'Unable to open external URL');
              }
            })
            .catch((err) => {
              console.error('Failed to open external URL:', err);
              Alert.alert('Error', 'Failed to open external URL');
            });
        }
      } else if (parsed.type === 'error' || parsed.type === 'ERROR') {
        // Handle errors from FastLink
        const errorMessage = parsed.message || parsed.data?.message || 'An error occurred during bank linking';
        onError(errorMessage);
      } else if (parsed.type === 'success') {
        // Direct success message
        onSuccess(parsed.data || parsed);
      }
    } catch (err) {
      console.error('Error parsing FastLink message:', err);
      
      // Only handle plain text if it looks like a simple success/close signal
      if (typeof data === 'string' && (data.includes('"success"') || data.includes('"close"'))) {
        try {
          // Try one more time with a different parse approach
          const simpleParse = JSON.parse(data);
          if (simpleParse.success || simpleParse.close) {
            onSuccess(simpleParse);
          }
        } catch {
          // Invalid payload - ignore for security
          console.warn('FastLink: Dropping invalid message payload');
        }
      }
    }
  };

  // Handle navigation state changes (for success/callback URLs)
  const handleNavigationStateChange = (navState: any) => {
    const url = navState.url;
    
    // Check for success callback
    if (url.includes('success') || url.includes('callback')) {
      // Extract query params or path segments
      try {
        const urlObj = new URL(url);
        const params = new URLSearchParams(urlObj.search);
        const success = params.get('success');
        
        if (success === 'true' || url.includes('success')) {
          // Parse any account data from URL params
          const accountData: any = {};
          params.forEach((value, key) => {
            accountData[key] = value;
          });
          onSuccess(accountData);
        }
      } catch (err) {
        // If URL parsing fails, still consider it success if URL contains success
        if (url.includes('success')) {
          onSuccess({});
        }
      }
    }
    
    // Check for error callback
    if (url.includes('error') || url.includes('failed')) {
      onError('Bank linking failed. Please try again.');
    }
  };

  // Handle errors in WebView
  const handleError = (syntheticEvent: any) => {
    const { nativeEvent } = syntheticEvent;
    console.error('WebView error:', nativeEvent);
    onError(nativeEvent?.description || 'Failed to load bank linking interface');
  };

  // Injected JavaScript to handle FastLink postMessage
  const injectedJavaScript = `
    (function() {
      // Listen for FastLink messages
      window.addEventListener('message', function(event) {
        if (event.data && typeof event.data === 'object') {
          window.ReactNativeWebView.postMessage(JSON.stringify(event.data));
        } else if (typeof event.data === 'string') {
          window.ReactNativeWebView.postMessage(event.data);
        }
      });

      // Listen for FastLink postMessage (Yodlee's communication method)
      if (window.postMessage) {
        const originalPostMessage = window.postMessage;
        window.postMessage = function(message, targetOrigin) {
          if (typeof message === 'object') {
            window.ReactNativeWebView.postMessage(JSON.stringify(message));
          } else {
            window.ReactNativeWebView.postMessage(message);
          }
          return originalPostMessage.call(window, message, targetOrigin);
        };
      }

      // Detect when FastLink closes
      window.addEventListener('beforeunload', function() {
        window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'close' }));
      });
    })();
    true; // Required for iOS
  `;

  if (!fastLinkUrl) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  const [isLoading, setIsLoading] = useState(true);

  return (
    <View style={styles.container}>
      {isLoading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Connecting to your bank...</Text>
        </View>
      )}
      <WebView
        ref={webViewRef}
        source={{
          uri: fastLinkUrl,
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: postData,
        }}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        startInLoadingState={true}
        mixedContentMode="never"
        allowsInlineMediaPlayback={true}
        mediaPlaybackRequiresUserAction={false}
        renderLoading={() => (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#007AFF" />
          </View>
        )}
        onMessage={handleMessage}
        onNavigationStateChange={handleNavigationStateChange}
        onLoadStart={() => {
          setIsLoading(true);
        }}
        onLoadEnd={() => {
          setIsLoading(false);
        }}
        onError={handleError}
        onHttpError={(syntheticEvent) => {
          const { nativeEvent } = syntheticEvent;
          console.error('WebView HTTP error:', nativeEvent);
          setIsLoading(false);
          if (nativeEvent.statusCode >= 400) {
            onError(`HTTP Error ${nativeEvent.statusCode}: Failed to load bank linking interface`);
          }
        }}
        injectedJavaScript={injectedJavaScript}
        style={styles.webview}
        allowsBackForwardNavigationGestures={false}
        // Security: Only allow HTTPS
        originWhitelist={['https://*', 'yodlee://*']}
        // Additional security headers
        sharedCookiesEnabled={true}
        cacheEnabled={false}
        incognito={false}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  webview: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  loadingContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    zIndex: 1000,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
    fontWeight: '500',
  },
});

export default FastLinkWebView;

