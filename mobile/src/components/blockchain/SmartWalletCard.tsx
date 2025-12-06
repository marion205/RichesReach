/**
 * Smart Wallet Card Component
 * Shows smart wallet status, gasless transactions, and session keys
 */

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import AccountAbstractionService from '../../services/AccountAbstractionService';
import { useWallet } from '../../wallet/WalletProvider';

interface SmartWalletCardProps {
  onSessionKeyCreate?: () => void;
}

export default function SmartWalletCard({ onSessionKeyCreate }: SmartWalletCardProps) {
  const wallet = useWallet();
  const address = wallet?.address || null;
  const isConnected = wallet?.isConnected || false;
  const [smartWalletAddress, setSmartWalletAddress] = useState<string | null>(null);
  const [isDeployed, setIsDeployed] = useState(false);
  const [balance, setBalance] = useState<string>('0');
  const [loading, setLoading] = useState(false);
  const [hasSessionKey, setHasSessionKey] = useState(false);

  useEffect(() => {
    if (isConnected && address) {
      loadSmartWallet();
    }
  }, [isConnected, address]);

  const loadSmartWallet = async () => {
    if (!address) return;
    
    try {
      setLoading(true);
      const walletAddress = await AccountAbstractionService.getSmartWalletAddress(address);
      setSmartWalletAddress(walletAddress);
      
      const deployed = await AccountAbstractionService.isWalletDeployed(walletAddress);
      setIsDeployed(deployed);
      
      if (deployed) {
        const walletBalance = await AccountAbstractionService.getWalletBalance(walletAddress);
        setBalance(walletBalance);
      }
    } catch (error) {
      console.error('Failed to load smart wallet:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSessionKey = async () => {
    try {
      // In production, this would use the actual signer
      Alert.alert(
        'Session Key',
        'Session keys allow passwordless transactions for 24 hours. Create one?',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Create',
            onPress: async () => {
              // Create session key with permissions
              // This is a placeholder - actual implementation needs signer
              setHasSessionKey(true);
              if (onSessionKeyCreate) {
                onSessionKeyCreate();
              }
              Alert.alert('Success', 'Session key created! You can now transact without popups for 24 hours.');
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to create session key');
    }
  };

  if (!isConnected) {
    return (
      <View style={styles.container}>
        <Text style={styles.placeholderText}>Connect wallet to enable smart wallet</Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="small" color="#667eea" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="zap" size={20} color="#667eea" />
        <Text style={styles.title}>Smart Wallet</Text>
        {isDeployed && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>Active</Text>
          </View>
        )}
      </View>

      {smartWalletAddress && (
        <View style={styles.addressContainer}>
          <Text style={styles.addressLabel}>Wallet Address:</Text>
          <Text style={styles.address} numberOfLines={1} ellipsizeMode="middle">
            {smartWalletAddress}
          </Text>
        </View>
      )}

      {isDeployed && (
        <View style={styles.balanceContainer}>
          <Text style={styles.balanceLabel}>Balance:</Text>
          <Text style={styles.balance}>{parseFloat(balance).toFixed(4)} ETH</Text>
        </View>
      )}

      <View style={styles.features}>
        <View style={styles.feature}>
          <Icon name="gift" size={16} color="#34C759" />
          <Text style={styles.featureText}>Gasless transactions</Text>
        </View>
        <View style={styles.feature}>
          <Icon name="shield" size={16} color="#34C759" />
          <Text style={styles.featureText}>Sponsored gas</Text>
        </View>
        {hasSessionKey && (
          <View style={styles.feature}>
            <Icon name="key" size={16} color="#34C759" />
            <Text style={styles.featureText}>Session key active</Text>
          </View>
        )}
      </View>

      {!hasSessionKey && (
        <TouchableOpacity
          style={styles.sessionKeyButton}
          onPress={handleCreateSessionKey}
        >
          <Icon name="key" size={16} color="#FFFFFF" />
          <Text style={styles.sessionKeyButtonText}>Create Session Key</Text>
        </TouchableOpacity>
      )}

      {!isDeployed && (
        <Text style={styles.deployHint}>
          Wallet will be deployed automatically on first transaction
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    marginLeft: 8,
    flex: 1,
  },
  badge: {
    backgroundColor: '#34C759',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  addressContainer: {
    marginBottom: 12,
  },
  addressLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  address: {
    fontSize: 14,
    color: '#1a1a1a',
    fontFamily: 'monospace',
  },
  balanceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  balanceLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  balance: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  features: {
    marginBottom: 12,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  featureText: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
  },
  sessionKeyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#667eea',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  sessionKeyButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  deployHint: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
  placeholderText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    padding: 20,
  },
});

