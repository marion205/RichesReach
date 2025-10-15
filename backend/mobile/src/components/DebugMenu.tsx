/**
 * Debug Menu Component
 * Quick access to debugging tools
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  Platform,
} from 'react-native';
import ConnectivityScreen from './ConnectivityScreen';

interface DebugMenuProps {
  visible: boolean;
  onClose: () => void;
}

export const DebugMenu: React.FC<DebugMenuProps> = ({ visible, onClose }) => {
  const [showConnectivity, setShowConnectivity] = useState(false);

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>🔧 Debug Menu</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.menu}>
          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => setShowConnectivity(true)}
          >
            <Text style={styles.menuItemIcon}>🌐</Text>
            <View style={styles.menuItemContent}>
              <Text style={styles.menuItemTitle}>Connectivity Test</Text>
              <Text style={styles.menuItemSubtitle}>Test API endpoints</Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => {
              console.log('🔧 API Configuration:', {
                API_HTTP: require('../config/api').API_HTTP,
                API_GRAPHQL: require('../config/api').API_GRAPHQL,
                API_AUTH: require('../config/api').API_AUTH,
                API_WS: require('../config/api').API_WS,
                Platform: Platform.OS,
                __DEV__,
              });
              alert('Configuration logged to console');
            }}
          >
            <Text style={styles.menuItemIcon}>📋</Text>
            <View style={styles.menuItemContent}>
              <Text style={styles.menuItemTitle}>Log Configuration</Text>
              <Text style={styles.menuItemSubtitle}>Print API config to console</Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => {
              const { API_HTTP } = require('../config/api');
              fetch(`${API_HTTP}/health/`)
                .then(res => res.json())
                .then(data => {
                  alert(`Health Check: ${JSON.stringify(data, null, 2)}`);
                })
                .catch(err => {
                  alert(`Health Check Failed: ${err.message}`);
                });
            }}
          >
            <Text style={styles.menuItemIcon}>❤️</Text>
            <View style={styles.menuItemContent}>
              <Text style={styles.menuItemTitle}>Quick Health Check</Text>
              <Text style={styles.menuItemSubtitle}>Test server health</Text>
            </View>
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Use this menu to debug network issues before demos
          </Text>
        </View>
      </View>

      {showConnectivity && (
        <Modal
          visible={showConnectivity}
          animationType="slide"
          presentationStyle="fullScreen"
        >
          <View style={styles.connectivityContainer}>
            <View style={styles.connectivityHeader}>
              <TouchableOpacity
                onPress={() => setShowConnectivity(false)}
                style={styles.backButton}
              >
                <Text style={styles.backButtonText}>← Back</Text>
              </TouchableOpacity>
            </View>
            <ConnectivityScreen />
          </View>
        </Modal>
      )}
    </Modal>
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
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    fontSize: 18,
    color: '#666',
  },
  menu: {
    padding: 16,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  menuItemIcon: {
    fontSize: 24,
    marginRight: 16,
  },
  menuItemContent: {
    flex: 1,
  },
  menuItemTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  menuItemSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  connectivityContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  connectivityHeader: {
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  backButton: {
    padding: 8,
  },
  backButtonText: {
    fontSize: 16,
    color: '#007AFF',
  },
});

export default DebugMenu;
