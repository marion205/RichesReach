/**
 * Legal Document Viewer Component
 * Displays legal documents (Terms of Service, Privacy Policy, EULA, BCP) in a WebView
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Modal,
} from 'react-native';
import { WebView } from 'react-native-webview';
import { Ionicons } from '@expo/vector-icons';

interface LegalDocumentViewerProps {
  visible: boolean;
  onClose: () => void;
  documentType: 'terms' | 'privacy' | 'eula' | 'bcp';
  title: string;
}

const LegalDocumentViewer: React.FC<LegalDocumentViewerProps> = ({
  visible,
  onClose,
  documentType,
  title,
}) => {
  const [isLoading, setIsLoading] = useState(true);

  // Determine document source
  const getDocumentSource = () => {
    switch (documentType) {
      case 'terms':
        return { uri: 'https://richesreach.com/terms-of-service' };
      case 'privacy':
        return { uri: 'https://richesreach.com/privacy-policy' };
      case 'eula':
        return { uri: 'https://richesreach.com/eula' };
      case 'bcp':
        return { uri: 'https://richesreach.com/bcp' };
      default:
        return { uri: 'https://richesreach.com/terms-of-service' };
    }
  };

  // For local HTML files (if using bundled documents)
  const getLocalSource = () => {
    switch (documentType) {
      case 'terms':
        return require('../../terms-of-service.html');
      case 'privacy':
        return require('../../privacy-policy.html');
      case 'eula':
        return require('../../eula.html');
      case 'bcp':
        return require('../../bcp.html');
      default:
        return require('../../terms-of-service.html');
    }
  };

  // Try local first, fallback to remote
  const source = getDocumentSource();

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>{title}</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color="#1C1C1E" />
          </TouchableOpacity>
        </View>

        {/* WebView */}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#007AFF" />
            <Text style={styles.loadingText}>Loading document...</Text>
          </View>
        )}
        <WebView
          source={source}
          style={styles.webview}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          startInLoadingState={true}
          onLoadStart={() => setIsLoading(true)}
          onLoadEnd={() => setIsLoading(false)}
          onError={(syntheticEvent) => {
            const { nativeEvent } = syntheticEvent;
            console.error('WebView error:', nativeEvent);
            setIsLoading(false);
          }}
        />
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    backgroundColor: '#FFFFFF',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    flex: 1,
  },
  closeButton: {
    padding: 4,
  },
  webview: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  loadingContainer: {
    position: 'absolute',
    top: 60,
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
  },
});

export default LegalDocumentViewer;

