/**
 * Wallet Connection Component
 * Handles wallet connection UI and state management
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import useWallet from '../../shared/hooks/useWallet';

interface WalletConnectionProps {
  onWalletConnected?: (walletInfo: any) => void;
  onWalletDisconnected?: () => void;
  style?: any;
}

const WalletConnection: React.FC<WalletConnectionProps> = ({
  onWalletConnected,
  onWalletDisconnected,
  style,
}) => {
  const {
    walletInfo,
    isConnected,
    isConnecting,
    error,
    connectWallet,
    disconnectWallet,
    switchNetwork,
  } = useWallet();

  const [isDisconnecting, setIsDisconnecting] = useState(false);

  const handleConnect = async () => {
    try {
      await connectWallet();
      onWalletConnected?.(walletInfo);
    } catch (err) {
      Alert.alert(
        'Connection Failed',
        'Failed to connect wallet. Please make sure you have MetaMask or another Web3 wallet installed.',
        [{ text: 'OK' }]
      );
    }
  };

  const handleDisconnect = async () => {
    setIsDisconnecting(true);
    try {
      disconnectWallet();
      onWalletDisconnected?.();
    } catch (err) {
      Alert.alert('Error', 'Failed to disconnect wallet', [{ text: 'OK' }]);
    } finally {
      setIsDisconnecting(false);
    }
  };

  const handleSwitchNetwork = async () => {
    try {
      // Switch to Ethereum Mainnet (chainId: 1)
      await switchNetwork(1);
    } catch (err) {
      Alert.alert(
        'Network Switch Failed',
        'Failed to switch to Ethereum Mainnet. Please switch manually in your wallet.',
        [{ text: 'OK' }]
      );
    }
  };

  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const formatBalance = (balance: string) => {
    const num = parseFloat(balance);
    return num.toFixed(4);
  };

  if (isConnected && walletInfo) {
    return (
      <View style={[styles.connectedContainer, style]}>
        <View style={styles.walletInfo}>
          <View style={styles.addressContainer}>
            <Icon name="wallet" size={16} color="#10B981" />
            <Text style={styles.addressText}>{formatAddress(walletInfo.address)}</Text>
          </View>
          
          {walletInfo.balance && (
            <View style={styles.balanceContainer}>
              <Text style={styles.balanceLabel}>Balance:</Text>
              <Text style={styles.balanceText}>{formatBalance(walletInfo.balance)} ETH</Text>
            </View>
          )}

          <View style={styles.chainContainer}>
            <Text style={styles.chainLabel}>Network:</Text>
            <Text style={styles.chainText}>
              {walletInfo.chainId === 1 ? 'Ethereum Mainnet' : `Chain ${walletInfo.chainId}`}
            </Text>
          </View>
        </View>

        <View style={styles.actions}>
          {walletInfo.chainId !== 1 && (
            <TouchableOpacity
              style={[styles.actionButton, styles.switchButton]}
              onPress={handleSwitchNetwork}
            >
              <Icon name="refresh-cw" size={16} color="#007AFF" />
              <Text style={styles.switchButtonText}>Switch Network</Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={[styles.actionButton, styles.disconnectButton]}
            onPress={handleDisconnect}
            disabled={isDisconnecting}
          >
            {isDisconnecting ? (
              <ActivityIndicator size="small" color="#EF4444" />
            ) : (
              <Icon name="log-out" size={16} color="#EF4444" />
            )}
            <Text style={styles.disconnectButtonText}>Disconnect</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.disconnectedContainer, style]}>
      <View style={styles.connectContent}>
        <Icon name="wallet" size={32} color="#6B7280" />
        <Text style={styles.connectTitle}>Connect Your Wallet</Text>
        <Text style={styles.connectSubtitle}>
          Connect your MetaMask or other Web3 wallet to access DeFi features
        </Text>

        {error && (
          <View style={styles.errorContainer}>
            <Icon name="alert-circle" size={16} color="#EF4444" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        <TouchableOpacity
          style={[styles.connectButton, isConnecting && styles.connectButtonDisabled]}
          onPress={handleConnect}
          disabled={isConnecting}
        >
          {isConnecting ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Icon name="link" size={20} color="#FFFFFF" />
          )}
          <Text style={styles.connectButtonText}>
            {isConnecting ? 'Connecting...' : 'Connect Wallet'}
          </Text>
        </TouchableOpacity>

        <Text style={styles.helpText}>
          Make sure you have MetaMask or another Web3 wallet installed
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  connectedContainer: {
    backgroundColor: '#F0FDF4',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#10B981',
  },
  walletInfo: {
    marginBottom: 12,
  },
  addressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  addressText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 8,
  },
  balanceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  balanceLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginRight: 8,
  },
  balanceText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  chainContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  chainLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginRight: 8,
  },
  chainText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  switchButton: {
    backgroundColor: '#EEF2FF',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  switchButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
    marginLeft: 4,
  },
  disconnectButton: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#EF4444',
  },
  disconnectButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#EF4444',
    marginLeft: 4,
  },

  disconnectedContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 24,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  connectContent: {
    alignItems: 'center',
  },
  connectTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginTop: 12,
    marginBottom: 8,
  },
  connectSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 16,
    lineHeight: 20,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF2F2',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
    color: '#EF4444',
    marginLeft: 8,
    flex: 1,
  },
  connectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
    marginBottom: 12,
  },
  connectButtonDisabled: {
    backgroundColor: '#9CA3AF',
  },
  connectButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    marginLeft: 8,
  },
  helpText: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
  },
});

export default WalletConnection;
